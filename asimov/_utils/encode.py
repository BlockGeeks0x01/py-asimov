import json
import functools

from web3.utils.contracts import encode_transaction_data as __encode_transaction_data
from web3.utils.abi import filter_by_name, filter_by_type
from eth_abi import encode_abi

from asimov.data_type import Account


encode_transaction_data = functools.partial(__encode_transaction_data, None)


class AsimovJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Account):
            return {"private_key": o.private_key, "public_key": o.public_key, "address": o.address}
        if isinstance(o, bytes):
            return o.decode('utf-8')
        return super().default(o)


def find_matching_func(contract_abi, fn_name, fn_type):
    """
    :param contract_abi:
    :param fn_name:
    :param fn_type:
    :return:
    {
        "inputs":[
            {
                "name":"_organizationName",
                "type":"string"
            },
            {
                "name":"_members",
                "type":"address[]"
            }
        ],
        "payable":true,
        "stateMutability":"payable",
        "type":"constructor",
        "name":"Association"
    }
    """
    if fn_name:
        abi = filter_by_name(fn_name, contract_abi)
    elif fn_type:
        abi = filter_by_type(fn_type, contract_abi)
    else:
        raise Exception("invalid parameters")

    if len(abi) == 0:
        raise Exception(f"no match function: {fn_name}")
    if len(abi) > 1:
        raise Exception(f"multiple match functions: {fn_name}")
    return abi[0]


def package_contract_func_args(contract_abi, fn_name, fn_type, args: list) -> list:
    """ setup parameter types according to abi"""
    abi = find_matching_func(contract_abi, fn_name, fn_type)

    for idx, _input in enumerate(abi['inputs']):
        if _input['type'].startswith('uint') or _input['type'].startswith('int'):
            args[idx] = int(args[idx])
    return args


def encode_params(contract_abi, fn_name, fn_type, args: list) -> str:
    abi = find_matching_func(contract_abi, fn_name, fn_type)
    args = package_contract_func_args(contract_abi, fn_name, fn_type, args)
    types = [e['type'] for e in abi['inputs']]
    return encode_abi(types, args).hex()
