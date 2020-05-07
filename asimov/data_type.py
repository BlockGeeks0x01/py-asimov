from collections import namedtuple
from pprint import pformat

from eth_utils.hexadecimal import remove_0x_prefix
from .constant import SUCCESS, FAILED


def __smart_contract_repr(c):
    return pformat({
        "abi": c.abi,
        "bytecode": c.bytecode,
        "address": c.address,
        "source": c.source
    })


SmartContract = namedtuple("SmartContract", ("source", "abi", "bytecode", "address"))
SmartContract.__new__.__defaults__ = (None,) * 4
SmartContract.__repr__ = __smart_contract_repr
SmartContract.__doc__ = "compiled contract"
SmartContract.source.__doc__ = "contract source code"
SmartContract.abi.__doc__ = "contract abi"
SmartContract.bytecode.__doc__ = "contract bytecode"
SmartContract.address.__doc__ = "contract address on chain"

ContractTemplate = namedtuple("ContractTemplate", ("template_name", "category", "source", "abi", "byte_code"))
ContractTemplate.__new__.__defaults__ = (None,) * 5
ContractTemplate.__doc__ = "contract template"
ContractTemplate.template_name.__doc__ = "template name"
ContractTemplate.category.__doc__ = "template category"
ContractTemplate.source.__doc__ = "template source code"
ContractTemplate.abi.__doc__ = "template abi"
ContractTemplate.byte_code.__doc__ = "template bytecode"


class Account:
    """
    Asimov account, consists of private key, public key and address
    """
    def __init__(self, private_key=None, address=None, public_key=None):
        self.private_key = private_key
        self.public_key = public_key
        self.address = address

    def __str__(self):
        return f"[{self.private_key}, {self.address}]"

    def __repr__(self):
        return self.__str__()


class Tx:
    """
    The primary entry point for working with transaction object.
    """

    def __init__(self, node, transaction, _id=None, is_contract_tx=False):
        self.node = node
        self.transaction = transaction
        self.signed_hex = transaction.sign().to_hex()
        self._id = _id
        self.is_contract_tx = is_contract_tx

    def __repr__(self):
        return f"[id: {self.id}]"

    @property
    def id(self) -> str:
        """
        get the transaction id
        """
        return self._id

    @id.setter
    def id(self, _id: str):
        """
        set the transaction id
        """
        self._id = _id

    def check(self) -> int:
        """
        check whether a normal transaction is confirmed on chain, or a contract call is successful or not
        
        :return: 1 if the transaction is confirmed on chain, or the contract call is successful
        """
        if self.is_contract_tx:
            return self.node.check(self.id)
        else:
            return SUCCESS if self.node.wait_for_confirmation(self.id) else FAILED

    def broadcast(self):
        """
        broadcast the transaction
        :return:
        """
        self._id = self.node._send_raw_trx(self.signed_hex)
        return self


class Asset:
    """
    The primary entry point for working with asset on asimov chain.

    Asimov asset consists of 3 parts

    #. asset_type, 4 bytes long, each bit contains an asset property. For now, the first bit is used to determine whether an asset is divisible and the second bit is used to determine whether the asset is restricted.
    #. org_id, 4 bytes long organization id, system wide unique id assigned to organization when registering to asimov platform.
    #. asset_index, 4 bytes long asset index in organization, the assigning rule is determined by the organization itself.
    """

    @staticmethod
    def asset_wrapper(asset_type, org_id, asset_index) -> int:
        """
        asimov asset wrapper

        :param asset_type: asset type.
        :param org_id: organization id.
        :param asset_index: asset index.
        :return: asimov asset id in int format

        .. code-block:: python

            >>> from asimov import Asset
            >>> Asset.asset_wrapper(0, 1, 1)
            4294967297
        """
        return (asset_type << 64) + (org_id << 32) + asset_index

    @staticmethod
    def asset2str(asset: int) -> str:
        """
        convert asset id from int to hex string without 0x
        :param asset: asset id in int format
        :return: asset id in hex string format

        .. code-block:: python

            >>> from asimov import Asset
            >>> Asset.asset2str(4294967297)
            '000000000000000100000001'
        """
        return remove_0x_prefix(hex(asset)).zfill(24)

    def __init__(self, contract, asset_type: int, asset_index: int):
        self.contract = contract
        self.org_id: int = self.contract.read("orgId")
        self.asset_type: int = asset_type
        self.asset_index: int = asset_index

    def __repr__(self):
        return f"[contract address: {self.contract.address}, asset: {self.asset_id_str} / {self.asset_id_int}]"

    @property
    def asset_id_int(self) -> int:
        """
        get the asset id in int format
        """
        return self.asset_wrapper(self.asset_type, self.org_id, self.asset_index)

    @property
    def asset_id_str(self) -> str:
        """
        get the asset id in hex string format
        """
        return self.asset2str(self.asset_id_int)


class EvmLog:
    """
    contract execution log
    """
    def __init__(self, raw_log):
        self.address = raw_log['address']
        self.block_hash = raw_log['blockHash']
        self.transaction_hash = raw_log['transactionHash']
        self.data = raw_log['data']
        self.topics: [str] = raw_log['topics']


class EvmLogs(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_dict(self) -> dict:
        """
        convert evm logs from list to dict, which may lose the logs of the same name
        :return: evm logs in dict format
        """
        return {item['name']: item['args'] for item in self}
