import json
import time
import copy
import math
from typing import Union

import requests
from eth_utils.address import remove_0x_prefix
from web3 import Web3

from .data_type import Account, Tx, ContractTemplate
from .account import AccountFactory
from . import error
from . import constant
from ._utils.encode import AsimovJsonEncoder, encode_transaction_data, encode_params
from ._utils.common import dict_add
from .transactions import Transaction


bytes_per_input = 148
gas_per_byte = 21


class Node:
    """
    A wrapped object for asimov node
    """
    def __init__(self, provider: str = None, private_key: str = None):
        self.session = requests.session()
        self.session.headers.update({"Content-type": "application/json"})
        self.provider = provider
        self.account: Account = AccountFactory.new(private_key)
        self.tx: Tx = None

    def __str__(self):
        return f"node[address:{self.address}]"

    def __repr__(self):
        return self.__str__()

    def set_rpc_server(self, url: str):
        """
        set rpc server url
        :param url: rpc server url
        """
        self.provider = url

    @staticmethod
    def _to_json(method: str, params: list = None):
        if not method.startswith(constant.RPC_PREFIX):
            method = constant.RPC_PREFIX + method
        data = {"id": int(time.time()), "jsonrpc": "2.0"}
        data.update({"method": method, "params": params})
        return data

    @property
    def address(self) -> str:
        """
        get the corresponding account address
        """
        return self.account.address

    @property
    def private_key(self):
        """
        get the account private key
        """
        return self.account.private_key

    def set_private_key(self, private_key: str):
        """
        set the account private key
        """
        self.account = AccountFactory.new(private_key)

    def call(self, method: str, args: list = None):
        """
        call asimov rpc service

        :param method: rpc function name
        :param args: rpc function arguments
        :return: the return value of the rpc function

        .. code-block:: python

            >>> from asimov import Node
            >>> node = Node("http://seed.asimov.tech")
            >>> node.call("getBlockChainInfo")
            {'chain': 'devnet',
             'blocks': 6841,
             'bestblockhash': '329a4289a46b5e6e6a7e63744338d63d9065c264a87f17c82bf13853806cc3ef',
             'mediantime': 1574942764,
             'pruned': False}
        """
        response = None
        try:
            if self.provider is None:
                raise Exception("provider is None")
            response = self.session.post(
                url=self.provider, data=json.dumps(self._to_json(method, args), cls=AsimovJsonEncoder))
            json_data = response.json()
            if "error" in json_data:
                raise error.RPCError(json_data['error']['message'])
            return json_data['result']
        except json.decoder.JSONDecodeError:
            if response:
                raise error.NetWorkError(response.content)
            raise error.JsonException()
        except KeyError as e:
            raise error.UnknownError(e)

    @staticmethod
    def create_contract_tx_output(address: str, amount: int, data: str, assets: str = constant.ASCOIN,
                                  contract_type=constant.TxType.CALL) -> dict:
        """
        create contract transaction output.
        in asimov, contract call is wrapped in transaction output.

        :param address: output address
        :param amount: output amount
        :param data: output data
        :param assets: output asset id in hex string format
        :param contract_type: contract call type, default is 'call'
        :return: output dict
        """
        return {
            "amount": amount,
            "address": address,
            "assets": assets,
            "contractType": contract_type,
            "data": data
        }

    @staticmethod
    def create_tx_output(address: str, amount: int, assets: str = constant.ASCOIN):
        """
        create transaction output.

        :param address: output address
        :param amount: output amount
        :param assets: output asset id in hex string format
        :return: output dict
        """
        return {
            "amount": amount,
            "address": address,
            "assets": assets
        }

    def balance(self, address: str = None, asset=constant.ASCOIN) -> Union[int, dict]:
        """
        get the balance of specific address by given asset type

        :param address: specific address, default is current node account address
        :param asset: asset type, will return balance for all asset types if none is given
        :return: balance of given asset type, or balance for all asset types
        """
        if address is None:
            address = self.address

        rst = self.call("getBalance", [address])
        if asset is not None:
            rst = [e for e in rst if e['asset'] == asset]
        if not rst:
            return 0
        for v in rst:
            v['value'] = int(v['value'])
        return rst[0]['value'] if asset is not None else rst

    def _get_tx_receipt(self, tx_id: str):
        return self.call("getTransactionReceipt", [tx_id])

    def check(self, tx_id: str) -> int:
        """
        If the transaction is a normal transaction, this function checks whether a transaction is confirmed on chain.
        If the transaction is a contract transaction, this function checks whether a transaction is confirmed on chain \
        and returns contract execution status.

        :param tx_id: transaction id
        :return: return 1 if the transaction is confirmed on chain and the execution result is success.

        .. code-block:: python

            >>> from asimov import Node, constant
            >>> node = Node(
                    "http://seed.asimov.tech",
                    "0xafd29358a5ba9e2f5aac5cd5013a6830a99e34a68c469c78ab5f4c6f1d8c2a46"
                )
            >>> tx = node.send("0x663bc0936166c07431ed04d7dc207eb7694e223ec4", asset_value=10)
            # wait tx on chain
            >>> assert tx.check() is constant.SUCCESS
        """
        assert self.wait_for_confirmation(tx_id) is True
        receipt = self._get_tx_receipt(tx_id)
        return int(receipt['status'], 16)

    def _get_utxo_in_page(self, address, asset, _from: int, count):
        """
        Get UTXO in page of a given address.

        :param address: the address to get UTXO from
        :param asset: asset type in hex string format
        :param from: start position of the page
        :param count: count of UTXO in the page
        :return: UTXO of specifc address by given asset type in page
        """

        rst = self.call("getUtxoInPage", [address, asset, _from, count])['utxos']
        return [item for item in rst if item['spendable'] is True]

    def _get_utxo(self, address: str, asset=constant.ASCOIN, amount=1):
        """
        Get UTXO with specific asset type and amount of a given address

        :param address: the address to get UTXO from
        :param asset: asset type, hex string format, default value is '000000000000'
        :param amount: asset amount, default is 1
        """
        amount = max([amount, 1])
        utxos = []
        utxo_pool = []
        current_amount = 0
        idx = 0
        while current_amount < amount:
            _utxos = self._get_utxo_in_page(address, asset, idx, 1000)
            if len(_utxos) == 0:
                raise error.NotEnoughMoney(utxos)
            _utxos = [utxo for utxo in _utxos if (utxo['txid'], utxo['vout']) not in utxo_pool]
            total_amount = sum([utxo['amount'] for utxo in _utxos])
            if total_amount + current_amount >= amount:
                for utxo in _utxos:
                    utxos.append(utxo)
                    current_amount += utxo['amount']
                    if current_amount >= amount:
                        return utxos
            else:
                utxos.extend(_utxos)
                utxo_pool.extend([(utxo['txid'], utxo['vout']) for utxo in _utxos])
                current_amount += total_amount
                idx += 1000

    def _send_raw_trx(self, signed_tx: str):
        """send signed raw transaction"""

        return self.call("sendRawTransaction", [signed_tx])

    def _get_raw_tx(self, tx_id: str, need_detail=False, need_extra=False):
        """get raw transaction detail by transaction id"""

        return self.call("getRawTransaction", [tx_id, need_detail, need_extra])

    def wait_for_confirmation(self, tx_id, confirm_num=1, timeout=60) -> bool:
        """
        wait for the transaction to be confirmed on chain

        :param tx_id: transaction id
        :param confirm_num: confirmed block count, default is 1
        :param timeout: time out length, default is 60 seconds
        :return: true if confirmed, false otherwise
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            rst = self._get_raw_tx(tx_id, True)
            if rst.get("confirmations", 0) >= confirm_num:
                return True
            time.sleep(1)
        return False

    def _get_best_block(self):
        """get the best block"""
        return self.call("getBestBlock")

    @property
    def current_height(self) -> int:
        """
        get the current height of chain
        """
        return self._get_best_block()['height']

    def _calc_contract_address(self, inputs: list, outputs: list):
        """
        calculate contract address from transaction inputs and outputs

        :param inputs: transaction inputs
        :param outputs: transaction outputs
        :return: contract address
        """
        outputs = copy.deepcopy(outputs)
        for output in outputs:
            output['amount'] = str(output['amount'])
        return self.call("calculateContractAddress", [inputs, outputs])['0']

    def get_contract_template(self, address: str = None, key: str = None, name: str = None) -> ContractTemplate:
        """
        get contract template object according to address, key or name

        :param address: contract address
        :param key: template key (template id)
        :param name: template name
        :return: the :class:`~asimov.data_type.ContractTemplate` object
        """
        if address:
            rst = self.call("getContractTemplate", [address])
            rst = self.call("getContractTemplateInfoByName", [1, rst['template_name']])
        elif key:
            rst = self.call("getContractTemplateInfoByKey", [key])
        elif name:
            rst = self.call("getContractTemplateInfoByName", [1, name])
        else:
            raise error.UnknownError()
        return ContractTemplate(rst['template_name'], rst['category'], rst['source'],
                                json.loads(rst['abi']), rst['byte_code'])

    def _call_readonly_function(self, contract_address: str, data: str, func_name: str,
                                abi: str, caller_address: str = None):
        """
        call a readonly function in a contract. a readonly function is marked as 'pure' or 'view'.

        :param contract_address: the contract to call
        :param data: binary data
        :param func_name: the function name to call
        :param abi: abi of the contract
        :param caller_address: the address to make the contract call
        """
        if caller_address is None:
            caller_address = self.address
        return self.call("callReadOnlyFunction", [caller_address, contract_address, data, func_name, abi])

    def _select_utxo(self, assets: dict) -> dict:
        """
        select UTXO according to given parameters
        """

        rst = dict()
        utxos = []

        for k, v in assets.items():
            if v == 0:
                continue
            _utxos = self._get_utxo(self.address, k, v)
            for _utxo in _utxos:
                _utxo['signed_key'] = self.account
            rst[k] = sum([_utxo['amount'] for _utxo in _utxos])
            utxos.extend(_utxos)
        rst['utxos'] = utxos

        return rst

    def _select_vote_utxo(self, vote_value: int, vote_asset_type: str, fees: dict) -> dict:
        """select UTXO for vote transaction"""
        assets = copy.copy(fees)
        if vote_value == 0:
            balance_of_vote_asset_type = self.balance(address=self.address, asset=vote_asset_type)
            if fees.get(vote_asset_type, 0) > balance_of_vote_asset_type:
                raise error.NotEnoughMoney(
                    f"need {assets[vote_asset_type]}, but only have {balance_of_vote_asset_type} of {vote_asset_type}")
            assets[vote_asset_type] = balance_of_vote_asset_type
        else:
            assets[vote_asset_type] = assets.get(vote_asset_type, 0) + vote_value
        return self._select_utxo(assets)

    def _build_transfer(
            self, address, asset_value, asset_type=constant.ASCOIN,
            tx_fee_type=constant.ASCOIN, gas_price=constant.DEFAULT_GAS_PRICE
    ) -> Transaction:
        """
        build a transaction
        """
        def __build_outputs(_select_rst: dict, _fee_value: int, _fee_type: str) -> list:
            needed_assets = dict_add({asset_type: asset_value}, {_fee_type: _fee_value})
            _outputs = [{
                "address": address,
                "amount": asset_value,
                "assets": asset_type
            }]
            # 找零 output
            for _asset_type in _select_rst:
                if _select_rst[_asset_type] > needed_assets[_asset_type]:
                    _outputs.append({
                        "address": self.address,
                        "amount": _select_rst[_asset_type] - needed_assets[_asset_type],
                        "assets": _asset_type
                    })
            return [item for item in _outputs if item['amount'] > 0]

        tx_fee_value = 0
        while True:
            select_rst = self._select_utxo(dict_add({asset_type: asset_value}, {tx_fee_type: tx_fee_value}))
            inputs = select_rst.pop('utxos')
            outputs = __build_outputs(select_rst, tx_fee_value, tx_fee_type)
            tx = Transaction(inputs, outputs)
            gas = self.estimate_gas(tx.sign().to_hex(), inputs)
            tx_fee_value = math.ceil(gas * gas_price)
            if select_rst.get(tx_fee_type, 0) >= (asset_value if asset_type == tx_fee_type else 0) + tx_fee_value:
                outputs = __build_outputs(select_rst, tx_fee_value, tx_fee_type)
                break
            tx_fee_value += math.ceil(bytes_per_input * gas_per_byte * gas_price)
        return Transaction(inputs, outputs, gas_limit=gas)

    def send(self, address, asset_value: int, asset_type=constant.ASCOIN, tx_fee_type=constant.ASCOIN) -> Tx:
        """
        send a normal transaction on asimov chain and return the transaction object :class:`~asimov.data_type.Tx`

        :param address: target address
        :param asset_value: asset value to send
        :param asset_type: asset type to send
        :param tx_fee_type: transaction fee type
        :return: the :class:`~asimov.data_type.Tx` object

        .. code-block:: python

            >>> from asimov import Node, constant
            >>> node = Node(
                    "http://seed.asimov.tech",
                    "0x98ca5264f6919fc12536a77c122dfaeb491ab01ed657c6db32e14a252a8125e3"
                )
            >>> node.send(
                    "0x663bc0936166c07431ed04d7dc207eb7694e223ec4",
                    asset_value=10, asset_type=constant.ASCOIN,
                    tx_fee_type=constant.ASCOIN
                )
            [id: 91c4645bcf3680c699a591632cd8769abe2973fd2de70081a6752d9781f2801b]
        """
        if asset_value < 1:
            raise error.InvalidParams(f"value should be larger than 1, got {asset_value}")
        return Tx(self, self._build_transfer(address, asset_value, asset_type, tx_fee_type)).broadcast()

    def call_write_function(
            self, func_name: str = None, params: tuple = None, abi=None, contract_address: str = constant.NullAddress,
            contract_tx_data=None, call_type=constant.TxType.CALL, asset_value=0, asset_type=constant.ASCOIN,
            tx_fee_type=constant.ASCOIN, gas_price=constant.DEFAULT_GAS_PRICE, corrected_gas=50000
    ) -> Tx:
        """
        send a transaction to execute a method in the contract

        :param func_name: function name to be called in the contract
        :param params: call parameters
        :param abi: contract abi
        :param contract_address: contract address
        :param contract_tx_data: binary data of the transaction
        :param call_type: call type
        :param asset_value: asset value to send
        :param asset_type: asset type to send
        :param tx_fee_type: transaction fee type
        :param gas_price: gas price
        :param corrected_gas: adjusted gas value
        :return: the :class:`~asimov.data_type.Tx` object
        """
        if call_type in (constant.TxType.TEMPLATE, constant.TxType.CREATE):
            assert contract_tx_data is not None
        if call_type in (constant.TxType.CALL, constant.TxType.VOTE) and contract_tx_data is None:
            contract_tx_data = remove_0x_prefix(
                encode_transaction_data(fn_identifier=func_name, contract_abi=abi, args=params)
            )
        contract_output = self.create_contract_tx_output(
            address=contract_address,
            amount=asset_value,
            data=contract_tx_data,
            assets=asset_type,
            contract_type=call_type
        )

        # estimate gas
        tx_fee_value = 0
        while True:
            if call_type == constant.TxType.VOTE:
                select_rst = self._select_vote_utxo(0, asset_type, {tx_fee_type: tx_fee_value})
            else:
                need_assets = dict_add({asset_type: asset_value}, {tx_fee_type: tx_fee_value})
                need_assets[tx_fee_type] = max([need_assets[tx_fee_type], 1])
                select_rst = self._select_utxo(need_assets)
            inputs = select_rst['utxos']
            outputs = [contract_output]
            if asset_type == tx_fee_type:
                outputs.append(self.create_tx_output(
                    self.address,
                    select_rst.get(asset_type, 0) - asset_value - tx_fee_value,
                    asset_type
                ))
            else:
                outputs.extend([
                    self.create_tx_output(self.address, select_rst.get(asset_type, 0) - asset_value, asset_type),
                    self.create_tx_output(self.address, select_rst.get(tx_fee_type, 0) - tx_fee_value, tx_fee_type)
                ])
            valid_outputs = [item for item in outputs if not (len(item.get("data", "")) == 0 and item['amount'] <= 0)]
            tx = Transaction(inputs, valid_outputs)
            gas = self.estimate_gas(tx.sign().to_hex(), inputs, corrected_gas)
            tx_fee_value = math.ceil(gas * gas_price)
            min_value = tx_fee_value
            if asset_type == tx_fee_type:
                min_value += asset_value
            if select_rst.get(tx_fee_type, 0) >= min_value:
                break
            tx_fee_value += math.ceil(bytes_per_input * gas_per_byte * gas_price)

        outputs = [contract_output]
        if asset_type == tx_fee_type:
            outputs.append(
                self.create_tx_output(
                    self.address, select_rst.get(asset_type, 0) - asset_value - tx_fee_value, asset_type)
            )
        else:
            outputs.extend([
                self.create_tx_output(self.address, select_rst.get(asset_type, 0) - asset_value, asset_type),
                self.create_tx_output(self.address, select_rst.get(tx_fee_type, 0) - tx_fee_value, tx_fee_type)
            ])
        valid_outputs = [item for item in outputs if not (len(item.get("data", "")) == 0 and item['amount'] <= 0)]
        return Tx(self, Transaction(select_rst['utxos'], valid_outputs, gas_limit=gas), is_contract_tx=True)

    def estimate_gas(self, tx_hex: str, inputs: list, corrected_value=50000):
        """
        estimate transaction execution gas cost
        :param tx_hex: transaction in hex format
        :param inputs: UTXO used in transaction
        :param corrected_value: corrected gas value
        :return:
        """
        rst = self.call("runTransaction", [tx_hex, inputs])
        return rst['gasUsed'] + corrected_value

    @staticmethod
    def build_data_of_deploy_contract(contract_template: ContractTemplate, params: list) -> str:
        """
        binary data for contract deployment transaction

        :param contract_template: the :class:`~asimov.data_type.ContractTemplate` object
        :param params: parameters of contract constructor function
        :return: transaction data
        """
        category_hex_str = remove_0x_prefix(hex(contract_template.category)).zfill(4)
        template_name_hex = bytes(contract_template.template_name, 'utf-8').hex()
        template_name_length_hex = str(len(contract_template.template_name)).zfill(8)

        params_hex = encode_params(contract_template.abi, None, constant.ContractFunType.CONSTRUCTOR, params)
        return category_hex_str + template_name_length_hex + template_name_hex + params_hex

    @staticmethod
    def build_data_of_create_template(category, name, hex_code, abi, source="solidity source code") -> str:
        """
        binary data for template creation transaction

        :param category: template category
        :param name: template name
        :param hex_code: transaction data in hex type
        :param abi: template abi
        :param source: template source code
        :return: transaction data
        """
        MAX = 0xffff
        if category >= MAX:
            category = MAX
        name_bytes: bytes = Web3.toBytes(text=name)
        bytecode_bytes = Web3.toBytes(hexstr=hex_code)
        if not isinstance(abi, str):
            abi = json.dumps(abi)
        abi_bytes: bytes = Web3.toBytes(text=abi)
        source_bytes: bytes = Web3.toBytes(text=source)
        return "".join([
            category.to_bytes(2, 'big', signed=False).hex(),
            len(name_bytes).to_bytes(4, 'big', signed=False).hex(),
            len(bytecode_bytes).to_bytes(4, 'big', signed=False).hex(),
            len(abi_bytes).to_bytes(4, 'big', signed=False).hex(),
            len(source_bytes).to_bytes(4, 'big', signed=False).hex(),
            name_bytes.hex(),
            hex_code,
            abi_bytes.hex(),
            source_bytes.hex()
        ])
