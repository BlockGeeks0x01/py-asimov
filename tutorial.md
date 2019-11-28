## Introduction

This document describes how to develop python script to test and deploy contracts on Asimov using high level Python API.

## Dependence

### Install Python Environment

Before running python script, you need to install python and set up your virtual environment. 
Follow instructions on [python.org](https://www.python.org/) and [pyenv](https://github.com/pyenv/pyenv) to finish the installation.
<br>
Asimov Python SDK has been fully tested on Python 3.7+.

### Install secp256k1
It is an optimized C library for EC operations on curve secp256k1.
Follow instructions on [specp256k1](https://github.com/bitcoin-core/secp256k1) to finish the installation.

> Note: If you see the error message like `Cannot import secp256k1: libsecp256k1.so.0: cannot open shared object file...`
> when execute `pip install py-asimov`.Let's assume `LIBDIR` is `/usr/local/lib`, then you can add `LIBDIR` to the `LD_LIBRARY_PATH` environment variable like
> `export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib` on Fedora/CentOS/RHEL.

### Install gmp for fastecdsa
Py-Asimov use [fastecdsa](https://pypi.org/project/fastecdsa/) library for fast elliptic curve crypto.
Note that you need to have a C compiler. You also need to have [GMP](https://gmplib.org/) on your system as the underlying C code in this package includes the `gmp.h` header (and links against gmp via the `-lgmp` flag). You can install all dependencies as follows:

#### apt
```shell script
$ apt-get install python-dev libgmp3-dev
```

#### yum
```shell script
$ yum install python-devel gmp-devel
```

#### mac
```shell script
$ brew install gmp
```

### Install Asimov Python SDK

```sh
pip install -i https://test.pypi.org/simple/ py-asimov
```

We provide high level Python API through JS SDK. Please visit [Python API](./python-api.md) to read api specifications.


### Install Asimov Smart Contract Compiler

Follow instructions on [Asimov](https://asimov.network) to finish the installation.



## Tutorial

We provide a [tutorial.py](./examples/tutorial.py) to cover the most used functions in Python SDK, 
including ***submit template***, ***deploy contract***, ***execute/vote on contract methods***, 
***read contract states*** and ***check transaction status*** and so on.

The smart contract test against in the above script is [tutorial.sol](./examples/contracts/tutorial.sol). 

### Initialize Node Instance

```python
from asimov import Node

node = Node() 
```

### Setup RPC Server and Private Key

```python
# set rpc server
node.set_rpc_server("http://seed.asimov.tech")

# set private key
node.set_private_key("your private key")
```

### Submit Template
```python
from asimov import Template
from asimov.constant import SUCCESS

# initialize template instance
t = Template(node)

# submit a contract template to Asimov blockchain
tx = t.submit("./contracts/tutorial.sol", "template_name", 'Tutorial')

# make sure the transaction is confirmed on chain before moving on to next step
assert tx.check() is SUCCESS
```

### Deploy Contract

```python
from asimov import Contract

# deploy a contract instance to Asimov blockchain
deploy_tx, contract_address = t.deploy_contract(tx.id)

# make sure the transaction is confirmed on chain before moving on to next step
assert tx.check() is SUCCESS

# initialize contract instance
contract = Contract(node, contract_address)
```

### Execute Contract Methods

```python
from asimov import constant

# mint asset
tx = contract.execute("mint", [10000 * constant.COIN])

# make sure the transaction is confirmed on chain and the contract execution is successful
assert tx.check() is constant.SUCCESS

# call contract's read only function.We get new asset type and convert to string type.
asset_type = Asset.asset2str(contract.read("assettype"))

# transfer asset
assert contract.execute("transfer", [node.address, 100 * constant.COIN]).check() is constant.SUCCESS

```

### Vote Contract Methods 

```python
# call the vote method to vote using the utxo asset mint in the above step
assert contract.vote("vote", [88], 1, asset_type).check() is constant.SUCCESS
```
