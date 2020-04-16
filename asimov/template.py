from .node import Node
from .solc import AsimovSolc
from .data_type import SmartContract, Tx
from .constant import ASCOIN, TxType


class Template:
    def __init__(self, node: Node):
        self.node = node

    def submit(self, source, template_name, chosen_contract, tx_fee_type=ASCOIN) -> Tx:
        """
        submit a new template to asimov blockchain and return the transaction object :class:`~asimov.data_type.Tx`

        :param source: smart contract source file path
        :param template_name: template name
        :param chosen_contract: contract name
        :param tx_fee_type: transaction fee type
        :return: the transaction object :class:`~asimov.data_type.Tx`

        .. code-block:: python

            >>> from asimov import Node, Template
            >>> node = Node("http://seed.asimov.tech", "0x98ca5264f6919fc12536a77c122dfaeb491ab01ed657c6db32e14a252a8125e3")
            >>> t = Template(node)
            >>> tx = t.submit("tutorial.sol", "template name1", "Tutorial")
            >>> tx
            [id: 8414ceb0d6db9c6418cd62c022168d961e69de80f662f0cdd99669f5954955ae]
            # template id
            >>> tx.id
            '8414ceb0d6db9c6418cd62c022168d961e69de80f662f0cdd99669f5954955ae'
        """
        compiled_contract: SmartContract = AsimovSolc.compile(source)[chosen_contract]
        tx_data = self.node.build_data_of_create_template(
            1, template_name, compiled_contract.bytecode, compiled_contract.abi, compiled_contract.source)
        return self.node.call_write_function(
            contract_tx_data=tx_data, call_type=TxType.TEMPLATE, tx_fee_type=tx_fee_type
        ).broadcast()

    def deploy_contract(self, template_id: str, constructor_arguments=None,
                        asset_value=0, asset_type=ASCOIN, tx_fee_type=ASCOIN) -> (Tx, str):
        """
        deploy a contract based on a given template id and
        return the address of the newly deployed contract on asimov blockchain and transaction object

        :param template_id: template id
        :param constructor_arguments: contract constructor arguments
        :param asset_value: asset value to send
        :param asset_type: asset type to send
        :param tx_fee_type: transaction fee type
        :return: the transaction object :class:`~asimov.data_type.Tx` and the address of new contract

        .. code-block:: python

            >>> from asimov import Node, Template, constant
            >>> node = Node("http://seed.asimov.tech", "0x98ca5264f6919fc12536a77c122dfaeb491ab01ed657c6db32e14a252a8125e3")
            >>> t = Template(node)
            >>> tx = t.submit("tutorial.sol", "template name1", "Tutorial")
            >>> assert tx.check() is constant.SUCCESS
            >>> t.deploy_contract(tx.id)
            [id: 2b7af42268f1ae098bc959d52c2c7d05af9cb44b2f2b6c8cfeb5c3afab941d5b]
        """
        if constructor_arguments is None:
            constructor_arguments = []
        contract_template = self.node.get_contract_template(key=template_id)
        tx_data = self.node.build_data_of_deploy_contract(contract_template, constructor_arguments)
        tx = self.node.call_write_function(
            contract_tx_data=tx_data, call_type=TxType.CREATE,
            asset_value=asset_value, asset_type=asset_type,
            tx_fee_type=tx_fee_type
        ).broadcast()
        address = self.node._calc_contract_address(tx.transaction.vin, tx.transaction.vout)
        return tx, address
