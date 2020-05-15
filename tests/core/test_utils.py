import json

import pytest
from asimov._utils.common import dict_add
from asimov._utils.encode import AsimovJsonEncoder, find_matching_func
from asimov.account import AccountFactory


@pytest.mark.parametrize("dicts,target", [
    ([{'a': 1, 'b': 1}], {'a': 1, 'b': 1}),
    ([{'a': 1, 'b': 1}, {'a': 99, 'c': 0}], {'a': 100, 'b': 1, 'c': 0}),
    ([{}], {}),
    ([{}, {}], {}),
    ([{'a': 1, 'b': 1}, {'a': 99, 'b': 2}], {'a': 100, 'b': 3}),
    ([{'a': 1}, {'a': -1}], {'a': 0}),
    ([{'a': 1}, {'b': -1}], {'a': 1, 'b': -1}),
])
def test_dict_add(dicts: list, target):
    assert dict_add(*dicts) == target


@pytest.mark.parametrize("obj", [
    {"account": AccountFactory.new(), "value": 1},
    {"account": AccountFactory.new(), "value": b'xxx'},
    {"account": AccountFactory.new(), "value": '测试'.encode("utf8")},
    {'name': 'xx', 'value': 1},
    {},
])
def test_encoder(obj):
    json.dumps(obj, cls=AsimovJsonEncoder)


@pytest.mark.parametrize("args, expect_rst", [
    [("send", None), {'constant': False, 'inputs': [], 'name': 'send', 'outputs': [], 'payable': True, 'stateMutability': 'payable', 'type': 'function'}],
    [(None, None), Exception()],
    [("send2", None), Exception()],
    [("withdraw", None), Exception()],
])
def test_find_matching_func(complied_contract, args, expect_rst):
    if type(expect_rst) == Exception:
        with pytest.raises(Exception):
            find_matching_func(complied_contract.abi, *args)
    else:
        assert find_matching_func(complied_contract.abi, *args) == expect_rst
