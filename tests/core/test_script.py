from web3 import Web3
from eth_utils import remove_0x_prefix
from asimov.constant import AsimovOpCode
from bitcointx.core import script


def test_scrip_op():
    expected = "c5"
    hex_value = script.CScript([script.CScriptOp(197)]).hex()
    assert hex_value == expected


def test_pub_key_script():
    expected = "76a9203197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48c5ac"
    hex_value = script.CScript([
        script.OP_DUP, script.OP_HASH160,
        Web3.toBytes(hexstr="0x3197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48"),
        AsimovOpCode.OP_IFLAG_EQUALVERIFY, script.OP_CHECKSIG
    ]).hex()
    assert hex_value == expected


def test_create_contract_hash_script():
    expected = 'c1'
    hex_value = script.CScript(AsimovOpCode.OP_CREATE.to_bytes(1, 'little')).hex()
    assert hex_value == expected


def test_vote_hash_script():
    expected = 'c6153197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48'
    hex_value = ''.join([
        script.CScript(AsimovOpCode.OP_VOTE.to_bytes(1, 'little')).hex(),
        script.CScript(AsimovOpCode.OP_DATA_21.to_bytes(1, 'little')).hex(),
        remove_0x_prefix(Web3.toHex(hexstr="0x3197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48"))
    ])
    assert hex_value == expected


def test_call_contract_hash_script():
    expected = 'c2203197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48'
    hex_value = script.CScript(AsimovOpCode.OP_CALL.to_bytes(1, 'little')).hex() + \
        len(
            Web3.toBytes(hexstr="0x3197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48")
        ).to_bytes(1, 'little', signed=False).hex() + \
        remove_0x_prefix(
            Web3.toHex(hexstr="0x3197eb7cd1538b26cf2398caa5986f1744934fb43e0b7f2a71c947bba0da3b48"))
    assert hex_value == expected
