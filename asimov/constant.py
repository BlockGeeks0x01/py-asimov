from bitcointx.core.script import CScriptOp

# Asim is the system asset of Asimov blockchain
ASCOIN = "000000000000000000000000"

SUCCESS = 1
FAILED = 0

RPC_PREFIX = 'asimov_'


# Xin is the smallest asset unit in Asimov, which is the same as satoshi in Bitcoin
# Coin = 100,000,000 Xin
XIN = 1
COIN = 100_000_000 * XIN

DEFAULT_GAS_PRICE = 0.1

NullAddress = "0x660000000000000000000000000000000000000000"


class TxType:
    """
    There are different call types when interacting with contract in a transaction

    #. CREATE deploy a new contract
    #. CALL call a contract function
    #. TEMPLATE submit a new template to template warehouse
    #. VOTE vote to a contact function
    """
    CREATE = "create"
    CALL = "call"
    TEMPLATE = "template"
    VOTE = "vote"


class AsimovOpCode:
    """new opcode added in asimov"""
    OP_DATA_21 = CScriptOp(21)
    OP_TEMPLATE = CScriptOp(192)
    OP_CREATE = CScriptOp(193)
    OP_CALL = CScriptOp(194)
    OP_SPEND = CScriptOp(195)
    OP_IFLAG_EQUAL = CScriptOp(196)
    OP_IFLAG_EQUALVERIFY = CScriptOp(197)
    OP_VOTE = CScriptOp(198)


class AddressType:
    """
    address types

    #. 0x66 normal account
    #. 0x63 contract
    """
    PubKeyHash = 0x66
    ContractHash = 0x63


class ContractFunType:
    """function types which follow EVM standards"""
    CONSTRUCTOR = "constructor"
    FUN = "function"
    FALLBACK = "fallback"
    EVENT = "event"


class UtxoSelectPolicy:
    NORMAL = 'normal'
    VOTE = 'vote'

