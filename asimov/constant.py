from bitcointx.core.script import CScriptOp


ASCOIN = "000000000000000000000000"


SUCCESS = 1
FAILED = 0


RPC_PREFIX = 'asimov_'


XIN = 1
COIN = 100_000_000 * XIN


NullAddress = "0x660000000000000000000000000000000000000000"


class TxType:
    CREATE = "create"
    CALL = "call"
    TEMPLATE = "template"
    VOTE = "vote"


class AsimovOpCode:
    OP_DATA_21 = CScriptOp(21)
    OP_TEMPLATE = CScriptOp(192)
    OP_CREATE = CScriptOp(193)
    OP_CALL = CScriptOp(194)
    OP_SPEND = CScriptOp(195)
    OP_IFLAG_EQUAL = CScriptOp(196)
    OP_IFLAG_EQUALVERIFY = CScriptOp(197)
    OP_VOTE = CScriptOp(198)


class AddressType:
    PubKeyHash = 0x66
    ContractHash = 0x63


class ContractFunType:
    CONSTRUCTOR = "constructor"
    FUN = "function"
    FALLBACK = "fallback"
    EVENT = "event"


class UtxoSelectPolicy:
    NORMAL = 'normal'
    VOTE = 'vote'

