import string
import random

from asimov import (
    AsimovSolc,
    Node,
    Template,
    constant,
    Contract,
    AccountFactory,
    Asset,
)


if __name__ == '__main__':
    # compile smart contract, need to install asimov solc firstly
    compiled_contract = AsimovSolc.compile("./contracts/tutorial.sol")['Tutorial']

    node = Node()
    # replace to your rpc server
    node.set_rpc_server("http://seed.asimov.tech")
    # node.set_rpc_server("http://localhost:8545")
    # replace to your private key
    # node.set_private_key("0x3197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48")
    node.set_private_key("0x98ca5264f6919fc12536a77c122dfaeb491ab01ed657c6db32e14a252a8125e3")
    # node.set_private_key("0xafd29358a5ba9e2f5aac5cd5013a6830a99e34a68c469c78ab5f4c6f1d8c2a46")

    # call rpc method
    print(f"my balance: {node.call('getBalance', [node.address])}")
    print(f"latest block info: {node.call('getBestBlock')}")

    # create template
    t = Template(node)
    template_name = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    tx = t.submit("./contracts/tutorial.sol", template_name, 'Tutorial')

    # wait for confirmation
    assert tx.check() is constant.SUCCESS

    # deploy contract
    org_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    deploy_tx, contract_address = t.deploy_contract(tx.id, [org_name])
    assert deploy_tx.check() is constant.SUCCESS
    print(f"contract address: {contract_address}")

    contract = Contract(node, contract_address)
    # contract = Contract(node, c=compiled_contract, args=[org_name])

    # mint asset
    assert contract.execute("mint", [10000 * constant.COIN]).check() is constant.SUCCESS
    # get asset type
    asset_type = Asset.asset2str(contract.read("assettype"))
    # check contract balance
    assert contract.read("checkBalance") == 10000 * constant.COIN
    # transfer asset from contract
    assert contract.execute("transfer", [node.address, 100 * constant.COIN]).check() is constant.SUCCESS
    assert node.balance(asset=asset_type) == 100 * constant.COIN
    # check contract balance
    assert contract.read("checkBalance") == 9900 * constant.COIN
    # transfer to other address
    assert node.send(AccountFactory.new().address, 1 * constant.COIN, asset_type).check() is constant.SUCCESS
    # check balance
    assert node.balance(asset=asset_type) == 99 * constant.COIN
    # burn
    assert contract.execute("burn", asset_value=98 * constant.COIN, asset_type=asset_type).check() is constant.SUCCESS
    # check balance
    assert node.balance(asset=asset_type) == 1 * constant.COIN

    assert contract.read("voteValues", [88]) == 0
    tx = contract.vote("vote", [88], asset_type=asset_type)
    assert tx.check() is constant.SUCCESS
    # check balance
    assert node.balance(asset=asset_type) == 1 * constant.COIN
    logs = contract.fetch(tx.id)
    # fetch logs
    print(logs)
    assert contract.read("voteValues", [88]) == 1 * constant.COIN







