import json
from unittest.mock import patch, Mock

import pytest
from requests import Session

from asimov import Node, Contract, constant, AsimovSolc, AccountFactory
from asimov.data_type import ContractTemplate


c = AsimovSolc.compile("tests/fixtures/Refund.sol")['Refund']
ct = ContractTemplate(
    template_name="test_template",
    category=1,
    source=c.source,
    abi=c.abi,
    byte_code=c.bytecode
)


class TestNode:
    @staticmethod
    def post(url, data):
        mock = Mock()
        post_data = json.loads(data)
        method = post_data['method'].split('_')[1]
        params = post_data['params']
        result = {}
        if method == "getContractTemplate":
            result = {"template_name": ct.template_name, "template_type": 1}
        elif method == "getContractTemplateInfoByName":
            result = {
                "category": 1,
                "template_name": ct.template_name,
                "byte_code": ct.byte_code,
                "abi": json.dumps(ct.abi),
                "source": ct.source
            }
        elif method == "getContractTemplateInfoByKey":
            result = {
                "category": 1,
                "template_name": ct.template_name,
                "byte_code": ct.byte_code,
                "abi": json.dumps(ct.abi),
                "source": ct.source
            }
        elif method == "callReadOnlyFunction":
            result = 1
        elif method == "calculateContractAddress":
            result = {'0': "0x6361d0441973eb4457d2f8092bbbe303db5eb0f981"}
        elif method == "getUtxoInPage":
            result = {'utxos': [{
                'txid': 'f93a2e011cf066877f6dc74c436af6715a8602eba360cd42d715a382fe92b7ed',
                'vout': 83, 'address': '0x66010e69d32d61872368f250652c70cace6d35db01',
                'height': 31264, 'scriptPubKey': '76a91566010e69d32d61872368f250652c70cace6d35db01c5ac',
                'amount': 100000000, 'confirmations': 1386, 'spendable': True,
                'assets': constant.ASCOIN, 'locks': None}]
            }
        elif method == "getBalance":
            result = [{"asset": constant.ASCOIN, "value": 100000000}]
        elif method == "runTransaction":
            result = {"gasUsed": 1}
        elif method == "sendRawTransaction":
            result = "ff882e011cf066877f6dc74c436af6715a8602eba360cd42d715a382fe92b7ed"
        elif method == "getRawTransaction":
            result = {
                "txid": "4930275d7d82676d7d2855d300a0e7b990c0f8327d9dae958ac56cabfada6d18",
                "hash": "4930275d7d82676d7d2855d300a0e7b990c0f8327d9dae958ac56cabfada6d18",
                "blockhash": "d999b02caa6dd0dd7cea55cd9a1d7bd4bfcbbfcd431fea5d8fb8304b42ec9cc2",
                "confirmations": 4607
            }
        elif method == "getTransactionReceipt":
            result = {
                "root": "0xe0faee16c5ff783cadc4ceb5e1e0587415e7b354351121b226d0da303671a892",
                "status": "0x1",
                "cumulativeGasUsed": "0x0",
                "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                "logs": [],
                "transactionHash": "22afe58927c8a7d8a25f10297db4a9a936a2beb68bb9a65a1667c2bb918b623a",
                "contractAddress": "0x000000000000000000000000000000000000000000",
                "gasUsed": "0x0"
            }
        elif method == "getBestBlock":
            result = {
                "hash": "d8dec197ec12aaf38db3739485e5ae517929059e2ddb1d0c6f59b77ded2a93a6",
                "height": 9999
            }
        mock.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": result}
        return mock

    def test_deploy(self, node: Node, complied_contract):
        with patch.object(Session, "post", side_effect=self.post):
            Contract(node, c=complied_contract)

    def test_deploy_according_template(self, node: Node, contract_template):
        mock_tx = Mock()
        mock_tx.broadcast().check.return_value = constant.SUCCESS

        with patch.multiple(
                node,
                get_contract_template=Mock(return_value=contract_template),
                call_write_function=Mock(return_value=mock_tx),
                _calc_contract_address=Mock(return_value="0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")
        ):
            Contract(node, template_name="test_template")

    def test_init_from_existing(self, node: Node):
        with patch.object(Session, "post", side_effect=self.post):
            Contract(node, "0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")

    def test_read_contract(self, node: Node):
        with patch.object(Session, "post", side_effect=self.post):
            contract = Contract(node, "0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")
            assert contract.read("dict", (0,)) == 1

    @pytest.mark.parametrize("call_type", ["write", "vote"])
    def test_execute_contract(self, node: Node, call_type):
        with patch.object(Session, "post", side_effect=self.post):
            contract = Contract(node, "0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")
            if call_type == "write":
                contract.execute("withdraw", (1000,))
            elif call_type == "vote":
                contract.vote("withdraw", (1000,))

    def test_parse_log(self, node: Node):
        with patch.object(Session, "post", side_effect=self.post):
            contract = Contract(node, "0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")
            logs = contract.fetch("6d1240e174059991087b43250caa920f559cff16d32863be75f02a1a0d781992")
            logs.to_dict()

    def test_send(self, node: Node):
        to_address = AccountFactory.new().address
        with patch.object(Session, "post", side_effect=self.post):
            assert node.send(to_address, 1).check() is constant.SUCCESS

    def test_current_height(self, node: Node):
        with patch.object(Session, "post", side_effect=self.post):
            assert node.current_height == 9999

