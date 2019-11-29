import json
import time
import copy

import requests
from eth_utils.address import remove_0x_prefix
from web3 import Web3

from .data_type import Account, Tx, ContractTemplate, SmartContract
from .account import AccountFactory
from . import error
from . import constant
from ._utils.encode import AsimovJsonEncoder, encode_transaction_data, encode_params
from .transactions import Transaction


class Node:
    def __init__(self, provider: str = None, private_key: str = None):
        self.session = requests.session()
        self.session.headers.update({"Content-type": "application/json"})
        self.provider = provider
        self.account: Account = AccountFactory.new(private_key)
        self.tx: Tx = None

    def __str__(self):
        return f"node[address:{self.address}]"

    def __repr__(self):
        return self.__str__()

    def set_rpc_server(self, url):
        self.provider = url

    @staticmethod
    def _to_json(method: str, params: list = None):
        if not method.startswith(constant.RPC_PREFIX):
            method = constant.RPC_PREFIX + method
        data = {"id": int(time.time()), "jsonrpc": "2.0"}
        data.update({"method": method, "params": params})
        return data

    @property
    def address(self):
        return self.account.address

    @property
    def private_key(self):
        return self.account.private_key

    def set_private_key(self, private_key):
        self.account = AccountFactory.new(private_key)

    def call(self, method: str, args: list = None):
        """
        call asimov rpc function

        :param method: rpc function name
        :param args: rpc function arguments
        :return: rpc function result

        .. code-block:: python

            >>> from asimov import Node
            >>> node = Node("http://seed.asimov.tech")
            >>> node.call("getBlockChainInfo")
            {'chain': 'devnet',
             'blocks': 6841,
             'bestblockhash': '329a4289a46b5e6e6a7e63744338d63d9065c264a87f17c82bf13853806cc3ef',
             'mediantime': 1574942764,
             'pruned': False}
        """
        response = None
        try:
            if self.provider is None:
                raise Exception("provider is None")
            response = self.session.post(
                url=self.provider, data=json.dumps(self._to_json(method, args), cls=AsimovJsonEncoder))
            json_data = response.json()
            if "error" in json_data:
                raise error.RPCError(json_data['error']['message'])
            return json_data['result']
        except json.decoder.JSONDecodeError:
            if response:
                raise error.NetWorkError(response.content)
            raise error.JsonException()
        except KeyError as e:
            raise error.UnknownError(e)

    @staticmethod
    def create_contract_tx_output(address: str, amount: int, data: str, assets: str = constant.ASCOIN,
                                  contract_type=constant.TxType.CALL) -> dict:
        return {
            "amount": amount,
            "address": address,
            "assets": assets,
            "contractType": contract_type,
            "data": data
        }

    @staticmethod
    def create_tx_output(address: str, amount: int, assets: str = constant.ASCOIN):
        return {
            "amount": amount,
            "address": address,
            "assets": assets
        }

    def get_balance(self, address: str, asset=None) -> [dict]:
        rst = self.call("getBalance", [address])
        if asset is not None:
            rst = [e for e in rst if e['asset'] == asset]
        for v in rst:
            v['value'] = int(float(v['value']) * constant.COIN)
        return rst

    def balance(self, address: str = None, asset=constant.ASCOIN) -> int:
        if address is None:
            address = self.address
        balances = self.get_balance(address, asset)
        if not balances:
            return 0
        return balances[0]['value']

    def _get_tx_receipt(self, tx_id: str):
        return self.call("getTransactionReceipt", [tx_id])

    def check(self, tx_id: str) -> int:
        """
        If the transaction is a normal transaction, this function checks wheter a transaction is confirmed on chain.
        If the transaction is a contract transaction, this function checks wheter a transaction is confirmed on chain and return contract execution status

        :param tx_id: transaction id
        :return:

        .. code-block:: python

            >>> from asimov import Node, constant
            >>> node = Node("http://seed.asimov.tech", "0xafd29358a5ba9e2f5aac5cd5013a6830a99e34a68c469c78ab5f4c6f1d8c2a46")
            >>> tx = node.send("0x663bc0936166c07431ed04d7dc207eb7694e223ec4", asset_value=10, tx_fee_value=1)
            # wait tx on chain
            >>> assert tx.check() is constant.SUCCESS
        """
        assert self.wait_for_confirmation(tx_id) is True
        receipt = self._get_tx_receipt(tx_id)
        return int(receipt['status'], 16)

    def _get_utxo_in_page(self, address, asset, _from: int, count):
        rst = self.call("getUtxoInPage", [address, asset, _from, count])['utxos']
        for item in rst:
            item['amount'] = int(item['amount'] * constant.COIN)
        return rst

    def _get_utxo(self, address: str, asset=constant.ASCOIN, amount=1):
        amount = max([amount, 1])
        utxos = []
        utxo_pool = []
        current_amount = 0
        idx = 0
        while current_amount < amount:
            _utxos = self._get_utxo_in_page(address, asset, idx, 1000)
            if len(_utxos) == 0:
                raise error.NotEnoughMoney(utxos)
            _utxos = [utxo for utxo in _utxos if (utxo['txid'], utxo['vout']) not in utxo_pool]
            total_amount = sum([utxo['amount'] for utxo in _utxos])
            if total_amount + current_amount >= amount:
                for utxo in _utxos:
                    utxos.append(utxo)
                    current_amount += utxo['amount']
                    if current_amount >= amount:
                        return utxos
            else:
                utxos.extend(_utxos)
                utxo_pool.extend([(utxo['txid'], utxo['vout']) for utxo in _utxos])
                current_amount += total_amount
                idx += 1000

    def _send_raw_trx(self, signed_tx: str):
        return self.call("sendRawTransaction", [signed_tx])

    def _get_raw_tx(self, tx_id: str, need_detail=False, need_extra=False):
        return self.call("getRawTransaction", [tx_id, need_detail, need_extra])

    def wait_for_confirmation(self, tx_id, confirm_num=1, timeout=60) -> bool:
        end_time = time.time() + timeout
        while time.time() < end_time:
            rst = self._get_raw_tx(tx_id, True)
            if rst.get("confirmations", 0) >= confirm_num:
                return True
            time.sleep(1)
        return False

    def _get_best_block(self):
        return self.call("getBestBlock")

    @property
    def current_height(self):
        return self._get_best_block()['height']

    def _calc_contract_address(self, inputs: list, outputs: list):
        outputs = copy.deepcopy(outputs)
        for output in outputs:
            output['amount'] = str(output['amount'])
        return self.call("calculateContractAddress", [inputs, outputs])['0']

    def get_contract_template(self, address=None, key=None, name=None) -> ContractTemplate:
        if address:
            rst = self.call("getContractTemplate", [address])
            rst = self.call("getContractTemplateInfoByName", [1, rst['template_name']])
        elif key:
            rst = self.call("getContractTemplateInfoByKey", [key])
        elif name:
            rst = self.call("getContractTemplateInfoByName", [1, name])
        else:
            raise error.UnknownError()
        return ContractTemplate(rst['template_name'], rst['category'], rst['source'],
                                json.loads(rst['abi']), rst['byte_code'])

    def call_readonly_function(self, contract_address: str, data: str, func_name: str,
                               abi: str, caller_address: str = None):
        if caller_address is None:
            caller_address = self.address
        return self.call("callReadOnlyFunction", [caller_address, contract_address, data, func_name, abi])

    def _select_utxo(self, asset_value, asset_type, tx_fee_value, tx_fee_type,
                     policy=constant.UtxoSelectPolicy.NORMAL) -> dict:
        rst = dict()
        rst[asset_type] = 0
        rst[tx_fee_type] = 0

        asset_value = max([asset_value, 1])
        if policy == constant.UtxoSelectPolicy.NORMAL:
            if tx_fee_value == 0:
                utxos = self._get_utxo(self.address, asset_type, asset_value)
            else:
                if asset_type == tx_fee_type:
                    utxos = self._get_utxo(self.address, asset_type, asset_value + tx_fee_value)
                else:
                    utxos = self._get_utxo(self.address, asset_type, asset_value)
                    utxos.extend(self._get_utxo(self.address, tx_fee_type, tx_fee_value))

        elif policy == constant.UtxoSelectPolicy.VOTE:
            vote_value = asset_value
            if vote_value == 0:
                vote_value = self.balance(asset=asset_type)
            if tx_fee_value == 0:
                try:
                    utxos = self._get_utxo(self.address, asset_type, vote_value)
                except error.NotEnoughMoney as e:
                    utxos = e.args[0]
            else:
                if tx_fee_value > self.balance(asset=tx_fee_type):
                    raise error.NotEnoughMoney()

                if asset_type == tx_fee_type:
                    try:
                        utxos = self._get_utxo(self.address, asset_type, vote_value + tx_fee_value)
                    except error.NotEnoughMoney as e:
                        utxos = e.args[0]
                else:
                    try:
                        utxos = self._get_utxo(self.address, asset_type, vote_value)
                    except error.NotEnoughMoney as e:
                        utxos = e.args[0]
                    utxos.extend(self._get_utxo(self.address, tx_fee_type, tx_fee_value))
        else:
            raise error.UnknownError(f"unknown utxo select policy: {policy}")

        for utxo in utxos:
            utxo['signed_key'] = self.account
        rst[asset_type] = sum([utxo['amount'] for utxo in utxos if utxo['assets'] == asset_type])
        rst[tx_fee_type] = sum([utxo['amount'] for utxo in utxos if utxo['assets'] == tx_fee_type])
        rst['utxos'] = utxos
        return rst

    def __build_transfer(
            self, address, asset_value, asset_type=constant.ASCOIN,
            tx_fee_value=0, tx_fee_type=constant.ASCOIN
    ) -> (list, list):
        select_rst = self._select_utxo(asset_value, asset_type, tx_fee_value, tx_fee_type)
        outputs = [self.create_tx_output(address, asset_value, asset_type)]
        if asset_type == tx_fee_type:
            outputs.append(
                self.create_tx_output(self.address, select_rst[asset_type] - asset_value - tx_fee_value, asset_type)
            )
        else:
            outputs.append(self.create_tx_output(self.address, select_rst[asset_type] - asset_value, asset_type))
            outputs.append(self.create_tx_output(self.address, select_rst[tx_fee_type] - tx_fee_value, tx_fee_type))
        vin_assets = [utxo['assets'] for utxo in select_rst['utxos']]
        outputs = [output for output in outputs if output['assets'] in vin_assets]
        return select_rst['utxos'], outputs

    def send(self, address, asset_value: int, asset_type=constant.ASCOIN,
             tx_fee_value=0, tx_fee_type=constant.ASCOIN) -> Tx:
        """
        sends a normal transaction on asimov blockchain and returns the transaction object :class:`~asimov.data_type.Tx`

        :param address:
        :param asset_value:
        :param asset_type:
        :param tx_fee_value:
        :param tx_fee_type:
        :return:

        .. code-block:: python

            >>> from asimov import Node, constant
            >>> node = Node("http://seed.asimov.tech", "0x98ca5264f6919fc12536a77c122dfaeb491ab01ed657c6db32e14a252a8125e3")
            >>> node.send("0x663bc0936166c07431ed04d7dc207eb7694e223ec4", asset_value=10, asset_type=constant.ASCOIN, tx_fee_value=1, tx_fee_type=constant.ASCOIN)
        """
        if asset_value < 1:
            raise error.InvalidParams(f"need large than 1, got {asset_value}")
        tx = Transaction(*self.__build_transfer(address, asset_value, asset_type, tx_fee_value, tx_fee_type))
        return Tx(node=self, _id=self._send_raw_trx(tx.sign().to_hex()))

    def call_write_function(
            self, func_name: str = None, params: tuple = None, abi=None, contract_address: str = constant.NullAddress,
            contract_tx_data=None, contract_type=constant.TxType.CALL, asset_value=0, asset_type=constant.ASCOIN,
            tx_fee_value=0, tx_fee_type=constant.ASCOIN
    ):
        select_policy = constant.UtxoSelectPolicy.VOTE if contract_type == constant.TxType.VOTE \
            else constant.UtxoSelectPolicy.NORMAL
        select_rst = self._select_utxo(asset_value, asset_type, tx_fee_value, tx_fee_type, select_policy)

        if contract_type == constant.TxType.VOTE:
            vote_value = asset_value
            asset_value = 0

        if contract_tx_data is None:
            contract_tx_data = remove_0x_prefix(
                encode_transaction_data(fn_identifier=func_name, contract_abi=abi, args=params)
            )
        outputs = [self.create_contract_tx_output(
            address=contract_address,
            amount=asset_value,
            data=contract_tx_data,
            assets=asset_type,
            contract_type=contract_type
        )]
        if asset_type == tx_fee_type:
            outputs.append(
                self.create_tx_output(self.address, select_rst[asset_type] - asset_value - tx_fee_value, asset_type)
            )
        else:
            outputs.append(self.create_tx_output(self.address, select_rst[asset_type] - asset_value, asset_type))
            outputs.append(self.create_tx_output(self.address, select_rst[tx_fee_type] - tx_fee_value, tx_fee_type))
        vin_assets = [utxo['assets'] for utxo in select_rst['utxos']]
        outputs = [output for output in outputs if output['assets'] in vin_assets]

        self.build_tx(select_rst['utxos'], outputs)
        if contract_type == constant.TxType.CALL:
            gas = self.estimate_call_contract_gas(
                SmartContract(abi=abi, address=contract_address), func_name, params, asset_value, asset_type
            )
        elif contract_type == constant.TxType.VOTE:
            gas = self.estimate_vote_gas(
                SmartContract(abi=abi, address=contract_address), func_name, vote_value, params, asset_type
            )
        elif contract_type == constant.TxType.TEMPLATE:
            gas = self.estimate_create_template_gas(contract_tx_data, asset_value, asset_type)
        elif contract_type == constant.TxType.CREATE:
            gas = self.estimate_deploy_contract_gas(contract_tx_data, asset_value, asset_type)
        else:
            raise error.InvalidTxType(contract_type)
        self.gas_limit(int(gas * 1))
        return self

    def estimate_call_contract_gas(self, contract: SmartContract, func_name, params=None,
                                   asset_value=0, asset_type=constant.ASCOIN):
        data = remove_0x_prefix(encode_transaction_data(
            fn_identifier=func_name, contract_abi=contract.abi, args=params))
        return self.call(
            "estimateGas",
            [self.address, contract.address, asset_value, asset_type, data, constant.TxType.CALL, 0]
        )

    def estimate_deploy_contract_gas(self, data, asset_value=0, asset_type=constant.ASCOIN):
        return self.call(
            "estimateGas",
            [self.address, constant.NullAddress, asset_value, asset_type, data, constant.TxType.CREATE, 0]
        )

    def estimate_create_template_gas(self, data, asset_value=0, asset_type=constant.ASCOIN):
        return self.call(
            "estimateGas",
            [self.address, constant.NullAddress, asset_value, asset_type, data, constant.TxType.TEMPLATE, 0]
        )

    def estimate_vote_gas(self, contract: SmartContract, func_name, vote_value, params=None, asset_type=constant.ASCOIN):
        data = remove_0x_prefix(encode_transaction_data(
            fn_identifier=func_name, contract_abi=contract.abi, args=params))
        return self.call(
            "estimateGas",
            [self.address, contract.address, 0, asset_type, data, constant.TxType.VOTE, vote_value]
        )

    @staticmethod
    def build_data_of_deploy_contract(contract_template: ContractTemplate, params: list) -> str:
        category_hex_str = remove_0x_prefix(hex(contract_template.category)).zfill(4)
        template_name_hex = bytes(contract_template.template_name, 'utf-8').hex()
        template_name_length_hex = str(len(contract_template.template_name)).zfill(8)

        params_hex = encode_params(contract_template.abi, None, constant.ContractFunType.CONSTRUCTOR, params)
        return category_hex_str + template_name_length_hex + template_name_hex + params_hex

    @staticmethod
    def build_data_of_create_template(category, name, hex_code, abi, source="solidity source code") -> str:
        MAX = 0xffff
        if category >= MAX:
            category = MAX
        name_bytes: bytes = Web3.toBytes(text=name)
        bytecode_bytes = Web3.toBytes(hexstr=hex_code)
        if not isinstance(abi, str):
            abi = json.dumps(abi)
        abi_bytes: bytes = Web3.toBytes(text=abi)
        source_bytes: bytes = Web3.toBytes(text=source)
        return "".join([
            category.to_bytes(2, 'big', signed=False).hex(),
            len(name_bytes).to_bytes(4, 'big', signed=False).hex(),
            len(bytecode_bytes).to_bytes(4, 'big', signed=False).hex(),
            len(abi_bytes).to_bytes(4, 'big', signed=False).hex(),
            len(source_bytes).to_bytes(4, 'big', signed=False).hex(),
            name_bytes.hex(),
            hex_code,
            abi_bytes.hex(),
            source_bytes.hex()
        ])

    def build_tx(self, inputs: list, outputs: list):
        is_contract_tx = outputs[0].get("contractType") is not None
        self.tx = Tx(self, vin=inputs, vout=outputs, is_contract_tx=is_contract_tx)
        return self

    def gas_limit(self, v: int):
        self.tx.gas_limit = v
        return self.tx

    def broadcast(self) -> Tx:
        """equal to sign & send"""
        tx = self.tx
        tx.id = self._send_raw_trx(Transaction(self.tx.vin, self.tx.vout, gas_limit=self.tx.gas_limit).sign().to_hex())
        return tx
