import pytest
from asimov.data_type import ContractTemplate, SmartContract
from asimov import AsimovSolc, Node, AccountFactory


@pytest.fixture(scope="session")
def contract_template(complied_contract: SmartContract) -> ContractTemplate:
    return ContractTemplate(
        template_name="test_template",
        category=1,
        source=complied_contract.source,
        abi=complied_contract.abi,
        byte_code=complied_contract.bytecode
    )


@pytest.fixture(scope="session")
def complied_contract() -> SmartContract:
    return AsimovSolc.compile("tests/fixtures/Refund.sol")['Refund']


@pytest.fixture(scope="session")
def node() -> Node:
    n = Node(private_key=AccountFactory.new().private_key)
    n.set_rpc_server("xxx")
    return n
