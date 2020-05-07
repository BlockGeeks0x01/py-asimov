from unittest.mock import MagicMock, patch

from asimov import Template
from asimov import Node


def test_submit():
    node = Node()
    node.call_write_function = MagicMock()
    t = Template(node)
    t.submit("tests/fixtures/Refund.sol", "template_name", "Refund")


def test_deploy_contract(node: Node, contract_template):
    with patch.multiple(
        node,
        get_contract_template=MagicMock(return_value=contract_template),
        call_write_function=MagicMock,
        _calc_contract_address=MagicMock(return_value="0x6361d0441973eb4457d2f8092bbbe303db5eb0f981")
    ):
        t = Template(node)
        t.deploy_contract("43e23d67f6a5a9b4e6be4e808afb54e3e2bc9c549c20610589ecc5154efae172")
