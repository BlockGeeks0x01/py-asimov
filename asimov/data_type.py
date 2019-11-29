from collections import namedtuple
from eth_utils.hexadecimal import remove_0x_prefix
from .constant import SUCCESS, FAILED


SmartContract = namedtuple("SmartContract", ("source", "abi", "bytecode", "address"))
SmartContract.__new__.__defaults__ = (None,) * 4
ContractTemplate = namedtuple("ContractTemplate", ("template_name", "category", "source", "abi", "byte_code"))
ContractTemplate.__new__.__defaults__ = (None,) * 5


class Account:
    def __init__(self, private_key=None, address=None, public_key=None):
        self.private_key = private_key
        self.public_key = public_key
        self.address = address

    def __str__(self):
        return f"[{self.private_key}, {self.address}]"

    def __repr__(self):
        return self.__str__()


class Tx:
    def __init__(self, node, _id=None, vin=None, vout=None, signed_hex=None, gas_limit=0, is_contract_tx=False):
        self.node = node
        self.vin = vin
        self.vout = vout
        self.gas_limit = gas_limit
        self._id = _id
        self.signed_hex = signed_hex
        self.is_contract_tx = is_contract_tx

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, _id):
        self._id = _id

    def __repr__(self):
        return f"[id: {self.id}]"

    def check(self) -> int:
        if self.is_contract_tx:
            return self.node.check(self.id)
        else:
            return SUCCESS if self.node.wait_for_confirmation(self.id) else FAILED


class Asset:
    @staticmethod
    def asset_wrapper(asset_type, org_id, asset_index) -> int:
        """
        asimov asset wrapper

        :param asset_type: asset type, the first bit of first byte, 0 is divided, 1 is undivided. The first bit of second byte, 0 if unvotable, 1 is votable.
        :param org_id: organization id
        :param asset_index: asset index in organization, should be equal
        :return: asset id
        """
        return (asset_type << 64) + (org_id << 32) + asset_index

    @staticmethod
    def asset2str(asset: int) -> str:
        return remove_0x_prefix(hex(asset)).zfill(24)

    def __init__(self, contract, asset_type: int, asset_index: int):
        self.contract = contract
        self.org_id: int = self.contract.read("orgId")
        self.asset_type: int = asset_type
        self.asset_index: int = asset_index

    def __repr__(self):
        return f"[contract address: {self.contract.address}, asset: {self.asset_id_str} / {self.asset_id_int}]"

    @property
    def asset_id_int(self):
        return self.asset_wrapper(self.asset_type, self.org_id, self.asset_index)

    @property
    def asset_id_str(self):
        return self.asset2str(self.asset_id_int)


class EvmLog:
    address: str = None
    block_hash: str = None
    transaction_hash: str = None
    data: str = None
    topics: [str] = None

    def __init__(self, raw_log):
        self.address = raw_log['address']
        self.block_hash = raw_log['blockHash']
        self.transaction_hash = raw_log['transactionHash']
        self.data = raw_log['data']
        self.topics = raw_log['topics']


class EvmLogs(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_dict(self):
        return {item['name']: item['args'] for item in self}
