import struct
from copy import deepcopy
from io import StringIO, BytesIO

from web3 import Web3
from eth_utils import remove_0x_prefix
from bitcointx.wallet import CBitcoinSecret
from bitcointx.core import script, b2lx, Hash
from bitcointx.core.serialize import VarIntSerializer

from .constant import TxType
from .data_type import Key
from .address import Address


DEFAULT_SEQUENCE = 0xffffffff


def VarIntSerializeSize(val: int) -> int:
    if val < 0xfd:
        return 1
    elif val <= (1 << 16 - 1):
        return 3
    elif val <= (1 << 32 - 1):
        return 5
    return 9


class TxInput:
    def __init__(self, vin: dict):
        self.prev_tx_id = vin['txid']
        self.vout = vin['vout']
        self.sequence = DEFAULT_SEQUENCE
        self.scriptPubKey = vin['scriptPubKey']
        self.sig_script = None
        self.signed_key: Key = vin.get('signed_key')     # 解锁这个输入脚本的key

    def write_buffer(self, buf):
        buf.write(self.prev_tx_id)
        buf.write(b2lx((self.vout).to_bytes(4, 'big', signed=False)))
        if self.sig_script:
            buf.write(VarIntSerializer.serialize(len(Web3.toBytes(hexstr=self.sig_script))).hex())
            buf.write(self.sig_script)
        else:
            buf.write(b'\x00'.hex())
        buf.write(b2lx((self.sequence).to_bytes(4, 'big', signed=False)))
        return buf

    def serialize_size(self) -> int:
        # Outpoint Hash 32 bytes + Outpoint Index 4 bytes + Sequence 4 bytes +
        # serialized varint size for the length of SignatureScript +
        # SignatureScript bytes
        length = len(self.sig_script) / 2 if self.sig_script else 0
        return 40 + length + VarIntSerializeSize(length)


class TxOutput:
    def __init__(self, output: dict):
        self.address = Address(output['address'])
        self.amount = output['amount']
        self.assets = output['assets']
        self.contract_type = output.get("contractType")
        self.data = output.get("data")
        self.pk_script = None
        if self.data:
            self.data = remove_0x_prefix(self.data)
            if self.contract_type == TxType.CALL:
                self.pk_script = self.address.to_contract_hash_script()
            elif self.contract_type == TxType.TEMPLATE:
                self.pk_script = self.address.to_create_template_hash_script()
            elif self.contract_type == TxType.CREATE:
                self.pk_script = self.address.to_create_contract_hash_script()
            elif self.contract_type == TxType.VOTE:
                self.pk_script = self.address.to_create_vote_hash_script()
            else:
                raise TypeError(f"unknown contract type: {self.contract_type}")
        else:
            if self.address.is_pay_to_contract_hash:
                self.pk_script = self.address.to_contract_hash_script()
            else:
                self.pk_script = self.address.to_script_pub_key()

    def write_buffer(self, buf):
        buf.write(b2lx(struct.pack(">q", self.amount)))
        buf.write(VarIntSerializer.serialize(len(Web3.toBytes(hexstr=self.pk_script))).hex())
        buf.write(self.pk_script)
        if self.assets:
            buf.write(VarIntSerializer.serialize(len(Web3.toBytes(hexstr=self.assets))).hex())
            buf.write(self.assets)
        else:
            buf.write(b'\x00'.hex())
        if self.data:
            buf.write(VarIntSerializer.serialize(len(Web3.toBytes(hexstr=self.data))).hex())
            buf.write(self.data)
        else:
            buf.write(b'\x00'.hex())
        return buf

    def serialize_size(self) -> int:
        # Value 8 bytes + Assets 12 byte
        # + serialized varint size for the length of PkScript +
        # PkScript bytes.
        # + serialized varint size for the length of Data +
        # Data bytes.
        pk_script_length = len(self.pk_script) / 2 if self.pk_script else 0
        data_length = len(self.data) / 2 if self.data else 0
        return 20 + VarIntSerializeSize(pk_script_length) + pk_script_length + VarIntSerializeSize(data_length) + data_length


class Transaction:
    def __init__(self, vin=(), vout=(), nLockTime=0, nVersion=1, gas_limit=0):
        if not (0 <= nLockTime <= 0xffffffff):
            raise ValueError('CTransaction: nLockTime must be in range 0x0 to 0xffffffff; got %x' % nLockTime)
        self.vin = vin
        self.vout = vout
        self.lock_time = nLockTime
        self.version = nVersion
        self.gas_limit = gas_limit
        self.inputs = [TxInput(_vin) for _vin in vin]
        self.outputs = [TxOutput(_vout) for _vout in vout]

    def to_buffer_writer(self) -> StringIO:
        buffer = StringIO()
        buffer.write(b2lx((self.version).to_bytes(4, 'big', signed=False)))
        buffer.write(b2lx(VarIntSerializer.serialize(len(self.inputs))))
        for _input in self.inputs:
            _input.write_buffer(buffer)
        buffer.write(b2lx(VarIntSerializer.serialize(len(self.outputs))))
        for _output in self.outputs:
            _output.write_buffer(buffer)
        buffer.write(b2lx((self.gas_limit).to_bytes(4, 'big', signed=False)))
        buffer.write(b2lx((self.lock_time).to_bytes(4, 'big', signed=True)))
        return buffer

    def to_hex(self) -> str:
        return self.to_buffer_writer().getvalue()

    def sign(self, sig_type=script.SIGHASH_ALL):
        for idx, _input in enumerate(self.inputs):
            assert _input.signed_key is not None
            _input.sig_script = AsimovScript.sign(self, _input.signed_key, idx, _input.scriptPubKey, sig_type).hex()
        return self

    def serialize_size(self) -> int:
        # Version 4 bytes + LockTime 4 bytes + TxContract 4 bytes + Serialized varint size for the
        # number of transaction inputs and outputs.
        n = 12 + VarIntSerializeSize(len(self.inputs)) + VarIntSerializeSize(len(self.outputs))
        for _input in self.inputs:
            n += _input.serialize_size()
        for _output in self.outputs:
            n += _output.serialize_size()
        return n

    @staticmethod
    def parse_sign_hex(sign_hex):
        """解析签名交易-16进制哈希"""
        # todo 假设vin,vou数量有限，都能用一个字节表示
        parse = list()
        parse.append(f"协议版本: {sign_hex[:8]}")
        parse.append(f"vin数量: {sign_hex[8:10]}")
        vin_num = Web3.toInt(hexstr=sign_hex[8:10])
        cursor = 10
        for n in range(vin_num):
            parse.append(f"第{n}组 vin")
            parse.append(f"vin hash: {sign_hex[cursor: cursor+64]}")
            parse.append(f"vin index: {sign_hex[cursor+64:cursor+64+8]}")
            cursor += 72
            parse.append(f"完整解锁脚本长度: {sign_hex[cursor: cursor+2]}")
            cursor += 2
            parse.append(f"解锁脚本长度: {sign_hex[cursor: cursor+2]}")
            redeem_script_length = Web3.toInt(hexstr=sign_hex[cursor: cursor+2])
            cursor += 2
            parse.append(f"解锁脚本: {sign_hex[cursor: cursor+(redeem_script_length-1)*2]}")
            cursor += (redeem_script_length-1)*2
            parse.append(f"签名类型: {sign_hex[cursor: cursor+2]}")
            cursor += 2
            parse.append(f"公钥长度: {sign_hex[cursor: cursor+2]}")
            public_key_length = Web3.toInt(hexstr=sign_hex[cursor: cursor+2])
            cursor += 2
            parse.append(f"解锁脚本的私钥对应的公钥: {sign_hex[cursor: cursor+public_key_length*2]}")
            cursor += public_key_length * 2
            parse.append(f"sequence: {sign_hex[cursor: cursor+8]}")
            cursor += 8
        parse.append(f"vout数量: {sign_hex[cursor: cursor+2]}")
        vout_num = Web3.toInt(hexstr=sign_hex[cursor: cursor+2])
        cursor += 2
        for n in range(vout_num):
            parse.append(f"第{n}组 vout")
            parse.append(f"amount: {sign_hex[cursor: cursor + 16]}")
            cursor += 16
            # todo 假设 pkscript长度 1个字节就能表示
            parse.append(f"pkscript长度: {sign_hex[cursor: cursor + 2]}")
            pkscript_length = Web3.toInt(hexstr=sign_hex[cursor: cursor + 2])
            cursor += 2
            parse.append(f"pkscript: {sign_hex[cursor: cursor + pkscript_length * 2]}")
            cursor += pkscript_length * 2
            parse.append(f"assets 长度: {sign_hex[cursor: cursor+ 2]}")
            assets_length = Web3.toInt(hexstr=sign_hex[cursor: cursor + 2])
            cursor += 2
            parse.append(f"pkscript: {sign_hex[cursor: cursor + assets_length * 2]}")
            cursor += assets_length * 2
            data_length = VarIntSerializer.deserialize(Web3.toBytes(hexstr=sign_hex[cursor:]))
            data_length_self_length = len(VarIntSerializer.serialize(data_length))
            parse.append(f"data 长度: {sign_hex[cursor: cursor+data_length_self_length * 2]}({data_length})")
            cursor += data_length_self_length * 2
            parse.append(f"data: {sign_hex[cursor: cursor + data_length * 2]}")
            cursor += data_length * 2
        parse.append(f"gas limit: {sign_hex[cursor: cursor+8]}")
        parse.append(f"lock time: {sign_hex[cursor+8: cursor+16]}")

        for msg in parse:
            print(msg)


class AsimovScript:
    @classmethod
    def SignatureHash(cls, tx: Transaction, in_idx, sub_script, hash_type=script.SIGHASH_ALL) -> bytes:
        tx = deepcopy(tx)
        for txin in tx.inputs:
            txin.sig_script = b''
        tx.inputs[in_idx].sig_script = sub_script
        s = Web3.toBytes(hexstr=tx.to_hex())
        s += struct.pack(b"<i", hash_type)
        return bytes(Hash(s))

    @classmethod
    def _sign(cls, key: Key, hashbuf, hash_type) -> bytes:
        sec_key = CBitcoinSecret.from_bytes(bytes.fromhex(remove_0x_prefix(key.private_key)))
        sig_script_bytes: bytes = sec_key.sign(hashbuf)
        sig_script_bytes += bytes([hash_type & 0xff])
        public_key = Web3.toBytes(hexstr=key.public_key.decode())

        script_buffer = BytesIO()
        script_buffer.write(bytes([len(sig_script_bytes)]))
        script_buffer.write(sig_script_bytes)
        script_buffer.write(bytes([len(public_key)]))
        script_buffer.write(public_key)
        return script_buffer.getvalue()

    @classmethod
    def sign(cls, tx: Transaction, key_pair: Key, in_idx, sub_script, hash_type=script.SIGHASH_ALL) -> bytes:
        hashbuf = cls.SignatureHash(tx, in_idx, sub_script, hash_type)
        sign_hash = cls._sign(key_pair, hashbuf, hash_type)
        return sign_hash
