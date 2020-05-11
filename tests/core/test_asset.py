from unittest.mock import Mock

from asimov import Asset, constant


def test_asset():
    assert Asset.asset_wrapper(0, 1, 1) == 4294967297
    assert Asset.asset2str(4294967297) == '000000000000000100000001'

    mock_contract = Mock()
    mock_contract.read.return_value = 1
    new_asset = Asset(mock_contract, 0, 1)
    print(new_asset)
    assert new_asset.asset_id_int == 4294967297
    assert new_asset.asset_id_str == '000000000000000100000001'
