import secrets
import hashlib
import codecs

from fastecdsa import (
    keys,
    curve
)
from eth_utils import (
    add_0x_prefix,
    remove_0x_prefix,
)
from web3 import Web3
from bitcointx.core import script

from .data_type import Key
from .constant import AddressType, AsimovOpCode


class PrivateKeyFactory:
    KEY_BYTES = 32
    CURVE_ORDER = int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141', 16)

    @classmethod
    def generate_key(cls) -> str:
        big_int = secrets.randbits(cls.KEY_BYTES * 8)
        big_int %= cls.CURVE_ORDER - 1
        big_int += 1
        key = hex(big_int)[2:].zfill(cls.KEY_BYTES * 2)
        return key


class KeyFactory:
    @classmethod
    def generate_address(cls, private_key: str) -> str:
        """
        :param private_key:
        :return: 没有0x前缀
        """
        public_key = cls.private2compressed_public(remove_0x_prefix(private_key))
        address = cls.__public2address(public_key)
        return address

    @classmethod
    def private2key_pair(cls, private_key: str) -> Key:
        public_key = cls.private2compressed_public(remove_0x_prefix(private_key))
        address = cls.__public2address(public_key)
        return Key(add_0x_prefix(private_key), add_0x_prefix(address), public_key)

    @classmethod
    def __private2public(cls, private_key: str) -> bytes:
        point = keys.get_public_key(Web3.toInt(hexstr=private_key), curve.secp256k1)
        public_key = '%s%s' % ('%064x' % int(point.x), '%064x' % int(point.y))
        return public_key.encode()

    @staticmethod
    def __add_bitcoin_byte(v: bytes) -> bytes:
        bitcoin_byte = b'04'
        return bitcoin_byte + v

    @classmethod
    def private2btc_public(cls, private_key: str) -> bytes:
        key_hex = cls.__private2public(private_key)
        return cls.__add_bitcoin_byte(key_hex)

    @classmethod
    def private2compressed_public(cls, private_key: str) -> bytes:
        key_hex = cls.__private2public(private_key)
        # get x from key (first half)
        key_string = str(key_hex, 'utf8')
        key_half = key_hex[:(len(key_hex) // 2)]
        # Add bitcoin byte: 0x02 if the last digit is even, 0x03 if the last digit is odd
        last_byte = int(key_string[-1], 16)
        btc_byte = b'02' if last_byte % 2 == 0 else b'03'
        public_key = btc_byte + key_half
        return public_key

    @classmethod
    def __public2address(cls, public_key: bytes) -> str:
        publick_key_bytes = codecs.decode(public_key, 'hex')
        # Run SHA256 for the public key
        sha256_bpk_digest = hashlib.sha256(publick_key_bytes).digest()
        # Run ripemd160 for the SHA256
        ripemd160_bpk = hashlib.new('ripemd160')
        ripemd160_bpk.update(sha256_bpk_digest)
        ripemd160_bpk_digest = ripemd160_bpk.digest()

        # asimov logic
        public_key_hash_addr_id = b'f'
        address_length = 21
        digest_length = len(ripemd160_bpk_digest)
        if digest_length > address_length - 1:
            ripemd160_bpk_digest = ripemd160_bpk_digest[digest_length + 1 - address_length:]
        ripemd160_bpk_digest = public_key_hash_addr_id + ripemd160_bpk_digest
        return str(codecs.encode(ripemd160_bpk_digest, 'hex'), 'utf8')

    @classmethod
    def new(cls, private_key=None) -> Key:
        if private_key is None:
            private_key = PrivateKeyFactory.generate_key()
        return cls.private2key_pair(private_key)


class Address:
    def __init__(self, address: str):
        self.address = address

    def __str__(self):
        return self.address

    def to_str(self):
        return self.address

    @property
    def type(self):
        return Web3.toInt(hexstr=remove_0x_prefix(self.address)[:2])

    @property
    def is_pay_to_contract_hash(self):
        return self.type == AddressType.ContractHash

    @property
    def is_pay_to_pub_hash(self):
        return self.type == AddressType.PubKeyHash

    def to_script_pub_key(self) -> str:
        return script.CScript([
            script.OP_DUP, script.OP_HASH160,
            Web3.toBytes(hexstr=self.address), AsimovOpCode.OP_IFLAG_EQUALVERIFY, script.OP_CHECKSIG
        ]).hex()

    @staticmethod
    def to_create_contract_hash_script():
        return script.CScript(AsimovOpCode.OP_CREATE.to_bytes(1, 'little')).hex()

    @staticmethod
    def to_create_template_hash_script():
        return script.CScript(AsimovOpCode.OP_TEMPLATE.to_bytes(1, 'little')).hex()

    def to_create_vote_hash_script(self):
        return ''.join([
            script.CScript(AsimovOpCode.OP_VOTE.to_bytes(1, 'little')).hex(),
            script.CScript(AsimovOpCode.OP_DATA_21.to_bytes(1, 'little')).hex(),
            remove_0x_prefix(Web3.toHex(hexstr=self.address))
        ])

    def to_contract_hash_script(self):
        return script.CScript(AsimovOpCode.OP_CALL.to_bytes(1, 'little')).hex() + \
               len(Web3.toBytes(hexstr=self.address)).to_bytes(1, 'little', signed=False).hex() + \
               remove_0x_prefix(Web3.toHex(hexstr=self.address))
