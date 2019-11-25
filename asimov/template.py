from .node import Node
from .asolc import AsimovSolc
from .data_type import SmartContract, Tx
from .constant import ASCOIN, TxType


class Template:
    def __init__(self, node: Node):
        self.node = node

    def submit(self, source, template_name, chosen_contract, tx_fee_value=0, tx_fee_type=ASCOIN) -> Tx:
        compiled_contract: SmartContract = AsimovSolc.compile(source)[chosen_contract]
        tx_data = self.node.build_data_of_create_template(
            1, template_name, compiled_contract.bytecode, compiled_contract.abi, compiled_contract.source)
        return self.node.call_write_function(
            contract_tx_data=tx_data, contract_type=TxType.TEMPLATE, tx_fee_value=tx_fee_value, tx_fee_type=tx_fee_type
        ).broadcast()

    def deploy_contract(self, template_id: str, constructor_arguments=None,
                        asset_value=0, asset_type=ASCOIN, tx_fee_value=0, tx_fee_type=ASCOIN) -> (Tx, str):
        if constructor_arguments is None:
            constructor_arguments = []
        contract_template = self.node.get_contract_template(key=template_id)
        tx_data = self.node.build_data_of_deploy_contract(contract_template, constructor_arguments)
        tx = self.node.call_write_function(
            contract_tx_data=tx_data, contract_type=TxType.CREATE,
            asset_value=asset_value, asset_type=asset_type,
            tx_fee_value=tx_fee_value, tx_fee_type=tx_fee_type
        ).broadcast()
        address = self.node.calc_contract_address(self.node.tx.vin, self.node.tx.vout)
        return tx, address
