import json
import random
import string
import functools

from eth_utils.hexadecimal import remove_0x_prefix

from .data_type import SmartContract, EvmLogs, Tx
from .node import Node
from .constant import ASCOIN, SUCCESS, TxType
from ._utils.encode import encode_transaction_data
from .vm_log import EvmLogParser


class Contract:
    def __init__(self, node: Node, address: str = None, c: SmartContract = None,
                 template_name: str = None, args: list = None):
        try:
            contract_template = node.get_contract_template(address=address, name=template_name)
        except:
            # create template firstly
            assert c is not None
            if template_name is None:
                template_name = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            tx_data = node.build_data_of_create_template(1, template_name, c.bytecode, c.abi, c.source)
            create_template_tx = node.call_write_function(
                contract_tx_data=tx_data, contract_type=TxType.TEMPLATE
            ).broadcast()
            assert create_template_tx.check() is SUCCESS
            contract_template = node.get_contract_template(key=create_template_tx.id)

        if address is None:
            tx_data = node.build_data_of_deploy_contract(contract_template, args if args else [])
            node.call_write_function(contract_tx_data=tx_data, contract_type=TxType.CREATE)
            address = node._calc_contract_address(node.tx.vin, node.tx.vout)
            assert node.broadcast().check() is SUCCESS

        self.template_name = contract_template.template_name
        self.address = address
        self.abi = contract_template.abi
        self.abi_json_str = json.dumps(self.abi)
        self.node: Node = node
        self.encode_tx_data = functools.partial(encode_transaction_data, contract_abi=self.abi)

    def __str__(self):
        return f"[address: {self.address}]"

    def __repr__(self):
        return self.__str__()

    def read(self, func_name, args=None):
        """
        calls a view method in the contract and returns the execution result
        :param func_name: view method function name
        :param args: function arguments
        :return: the result of the funciton

        .. code-block:: python

            >>> contract.read("checkBalance")
        """
        return self.node.call_readonly_function(
            contract_address=self.address,
            data=remove_0x_prefix(self.encode_tx_data(func_name, args=args)),
            func_name=func_name,
            abi=self.abi_json_str
        )

    def execute(self, func_name, args=None, asset_value=0, asset_type=ASCOIN,
                tx_fee_value=0, tx_fee_type=ASCOIN) -> Tx:
        """
        sends a transaction to execute a method in the contract and returns the transaction object :class:`~asimov.data_type.Tx`
        :param func_name: contract function name
        :param args: function arguments
        :param asset_value: the asset value to be send
        :param asset_type: the asset type to be send
        :param tx_fee_value: the transaction fee value
        :param tx_fee_type: the transaction fee type
        :return: the transaction object

        .. code-block:: python

            >>> tx = contract.execute("mint", [1000000])
            >>> tx.check()
        """
        return self.node.call_write_function(
            contract_address=self.address,
            params=args,
            func_name=func_name,
            abi=self.abi,
            asset_value=asset_value,
            asset_type=asset_type,
            tx_fee_value=tx_fee_value,
            tx_fee_type=tx_fee_type
        ).broadcast()

    def vote(self, func_name, args=None, vote_value=0, asset_type=ASCOIN, tx_fee_value=0, tx_fee_type=ASCOIN) -> Tx:
        """
        sends a transaction to vote on a contract and returns the transaction object :class:`~asimov.data_type.Tx`
        :param func_name:
        :param args:
        :param vote_value:
        :param asset_type:
        :param tx_fee_value:
        :param tx_fee_type:
        :return:

        .. code-block:: python

            >>> contract.vote("vote", [1]).check()
        """
        return self.node.call_write_function(
            contract_address=self.address,
            params=args,
            func_name=func_name,
            abi=self.abi,
            asset_type=asset_type,
            asset_value=vote_value,
            tx_fee_value=tx_fee_value,
            contract_type=TxType.VOTE,
            tx_fee_type=tx_fee_type
        ).broadcast()

    def fetch(self, tx_id) -> EvmLogs:
        """
        fetch the contract transaction execution logs
        :param tx_id: contract transaction id
        :return:
        """
        receipt = self.node._get_tx_receipt(tx_id)
        return EvmLogParser.parse(receipt['logs'], self.abi)
