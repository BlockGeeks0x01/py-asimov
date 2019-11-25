## Introduction   

This document describes high level Asimov Python API.

> Note that these high level APIs are a wrapper of [Asimov Restful API](https://gitlab.asimov.work/contracts/dapp-bin/blob/master/testnet-tutorial/docs/rpc.md) to provide a more easy to use interfaces. A python developer can choose to use restful api directly if willing to.

To use Asimov Python API, one must have **python3.7+** installed. With this library, you can do contract test/deploy script. However, you are free to utilize these APIs for other developing purposes.

We extract following high level modules in python API:

- Template
- Contract
- Transaction

all of which are built on top of the RPC and Setting modules.


## Node Object

Node object is a virtual asimov node. It is almost equivalent to restful api in python language. 
You can initialize a node object with rpc server url and private key.

```python
from asimov import Node
node = Node("http://localhost:8545", "0x3197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48")
# change rpc server url and private key when ever you want
node.set_rpc_server("http://you-rpc-server")
node.set_private_key("0x8dd839d5b978f113047ac9d08035ebf1b58ecd5ae6e92049f411e9d659be31f6")
```

```python
node.call(method, arguments)
```

- **method** rpc method to call.
- **arguments** arguments to call the given rpc method.

This function execute an rpc call directly agianst the set rpc server. 
More information on rpc methods, please refer to [Asimov Restful API](https://gitlab.asimov.work/contracts/dapp-bin/blob/master/testnet-tutorial/docs/rpc.md).

```python
node.send(address, asset_value, asset_type, tx_fee_value, tx_fee_type)
```

- **address** the recepient address.
- **assetvalue** the asset value to transfer.
- **asset_type** (***OPTIONAL***) asset type to transfer. ***If not set, it defaults to 0 which represents Asim.***
- **tx_fee_value** (***OPTIONAL***) transaction fee asset value. ***If not set, it defaults to 0.***
- **tx_fee_type** (***OPTIONAL***) transaction fee asset type. ***If not set, it defaults to 0 which represents Asim.***

This function sends a normal transaction on asimov blockchain and returns the transaction object.

## Asimov Smart Contract Object

Setting module provides methods to config default value for common settings. There are following functions in this module.

```python
from asimov import AsimovSolc
AsimovSolc.set_solidity_compiler(compiler)
```

- **compiler** solidity compiler bin file location.

This function sets the default solidity complier. You can install asimov compiler refer to [Asimov Compiler](https://asimov.network)

```python
AsimovSolc.compile(source)
```

- **source** contract source file path.


## Template Object

As introduced in [Contract Development Guide](https://gitlab.asimov.work/contracts/dapp-bin/blob/master/testnet-tutorial/docs/tutorial-contract.md), developers need to submit templates before deploying contracts. The precedure goes like this:

**Contract Source File** --submit--> **Asimov Template** --deploy--> **Contract Instance**

for the design purpose of asimov template, please read [Tech White Paper](https://doc.asimov.network/wp/template-design.html).

How to initialize a template module:

```python
from asimov import Template
Template = Template(node)
```

- **node** Node object.

There are two key functions of template module.

```python
submit(source, template_name, chosen_contract, tx_fee_value, tx_fee_type)
```

- **source** contract source file path.
- **template_name** template name.
- **chosen_contract** there could be more than 1 contract instance in the source file, you need to choose one when submitting a template. Input the contract name of the chosen contact.
- **tx_fee_value** (***OPTIONAL***) transaction fee asset value. ***If not set, it defaults to 0.***
- **tx_fee_type** (***OPTIONAL***) transaction fee asset type. ***If not set, it defaults to 0 which represents Asim.***

This function submits a new template to asimov blockchain and returns the template id of the newly submitted template. We use the corresponding transaction id as the template id.

```python
tx, contract_address = deploy_contract(template_id, constructor_arguments, asset_value, asset_type, tx_fee_value, tx_fee_type)
```

- **template_id** template id.
- **constructor_arguments** arguments for the constructor.
- **asset_value** (***OPTIONAL***) asset value to transfer to the contract. ***If not set, it defaults to 0.***
- **asset_type** (***OPTIONAL***) asset type to transfer to the contract. ***If not set, it defaults to 0 which represents Asim.***
- **tx_fee_value** (***OPTIONAL***) transaction fee asset value. ***If not set, it defaults to 0.***
- **tx_fee_type** (***OPTIONAL***) transaction fee asset type. ***If not set, it defaults to 0 which represents Asim.***

This function deploys a contract based on a given template id and returns the address of the newly deployed contract on asimov blockchain and transaction object.

## Contract Object

Web dapp development usually start with deployed contracts on Asimov chain. 
It can be done by either using [Web IDE](https://gitlab.asimov.work/contracts/dapp-bin/blob/master/testnet-tutorial/docs/ide-tool.md) or [Cmd Tool](https://gitlab.asimov.work/contracts/dapp-bin/blob/master/testnet-tutorial/docs/cmd.md) or the above Template Module API. 

How to initialize a Contract module:

```python
from asimov import Contract
contract = Contract(node, contract_address)
```

- **node** Node object.
- **contract_address** contract address.

or even more simply
```python
from asimov import AsimovSolc, Contract
compiled_contract = AsimovSolc.compile("./contracts/tutorial.sol")['Tutorial']
contract = Contract(node, c=compiled_contract)
```

- **c** complied contract object

There are four key functions of contract module.

```python
contract.execute(method, arguments, asset_value, asset_type, tx_fee_value, tx_fee_type)
```

- **method** method to call.
- **arguments** arguments for the method.
- **asset_value** (***OPTIONAL***) asset value to transfer to the contract. ***If not set, it defaults to 0.***
- **asset_type** (***OPTIONAL***) asset type to transfer to the contract. ***If not set, it defaults to 0 which represents Asim.***
- **tx_fee_value** (***OPTIONAL***) transaction fee asset value. ***If not set, it defaults to 0.***
- **tx_fee_type** (***OPTIONAL***) transaction fee asset type. ***If not set, it defaults to 0 which represents Asim.***

This function sends a transaction to execute a method in the contract and returns the transaction object.

```python
contract.vote(method, argument, asset_value, asset_type, tx_fee_value, tx_fee_type)
```

- **method** method to call.
- **arguments** arguments for the method.
- **votevalue** asset value to vote. If you want to vote all, set to 0.
- **asset_type** (***OPTIONAL***) asset type to transfer to the contract. ***If not set, it defaults to 0 which represents Asim.***
- **tx_fee_value** (***OPTIONAL***) transaction fee asset value. ***If not set, it defaults to 0.***
- **tx_fee_type** (***OPTIONAL***) transaction fee asset type. ***If not set, it defaults to 0 which represents Asim.***

This function sends a transaction to vote on a contract and returns the transaction object. Note the vote function may not vote the accurate value you set in the function since the policy is to consume whole vote value of chosen utxos.

```python
contract.read(method, arguments)
```

- **method** method to call.
- **arguments** arguments for the method.

This function calls a view method in the contract and returns the execution result.

```python
contract.fetch(tx_id)
```

- **tx_id** transaction id.

This function fetchs the logs during the contract execution.

## Transaction Object

It is relatively complicated to send a transaction and check transaction status on asimov blockchain using restful api direclty. As a result, we also provide a Transaction object to deal with these actions.

There is only one key functions of transaction object.

```python
tx_object.check()
```

If the transaction is a normal transaction, this function checks wheter a transaction is confirmed on chain and returns 1/0.
If the transaction is a contract transaction, this function checks wheter a transaction is confirmed on chain and return contract execution status.