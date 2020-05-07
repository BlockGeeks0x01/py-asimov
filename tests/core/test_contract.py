from unittest.mock import patch, Mock

from asimov import Node, Contract, constant


class TestContract:
    def test_deploy(self, node: Node, complied_contract, contract_template):
        mock_tx = Mock()
        mock_tx.broadcast().check.return_value = constant.SUCCESS

        def get_contract_template(address=None, name=None, key=None):
            if key:
                return contract_template
            raise Exception()

        with patch.multiple(
                node,
                get_contract_template=Mock(side_effect=get_contract_template),
                call_write_function=Mock(return_value=mock_tx),
                _calc_contract_address=Mock(return_value="0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")
        ):
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

    def test_init_from_existing(self, node: Node, contract_template):
        with patch.object(node, "get_contract_template", side_effect=Mock(return_value=contract_template)):
            Contract(node, "0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")