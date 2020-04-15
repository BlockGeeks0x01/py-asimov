from datetime import datetime


class _BaseException(Exception):
    def __repr__(self):
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.args}"

    def __str__(self):
        return self.__repr__()


class NoUtxoError(_BaseException):
    """no available utxo"""


class NotEnoughMoney(_BaseException):
    """not enough money"""


class JsonException(_BaseException):
    """json"""


class RPCError(_BaseException):
    """rpc response error"""


class NoAvailableKey(_BaseException):
    """no available key"""


class InvalidPrivateKey(_BaseException):
    """invalid private key"""


class CompileError(_BaseException):
    """compile error"""


class CompileTimeout(_BaseException):
    """compile timeout"""


class NetWorkError(_BaseException):
    """network error"""


class UnknownError(_BaseException):
    """Unknown"""


class UnSupportSolidityImportType(_BaseException):
    """solidity import error"""


class InvalidParams(_BaseException):
    """invalid parameters"""


class InvalidTxType(_BaseException):
    """invalid tx type"""
