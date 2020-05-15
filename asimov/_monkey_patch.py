import sys
import eth_utils

from eth_utils import address
from eth_abi.decoding import AddressDecoder


def uncache(exclude: [str]):
    pkgs = []
    to_uncache = []
    mod: str
    for mod in exclude:
        pkgs.append(mod.split('.', 1)[0])
    pkgs = list(set(pkgs))

    for mod in sys.modules:
        if mod in exclude:
            continue
        if mod in pkgs:
            to_uncache.append(mod)
            continue
        for pkg in pkgs:
            if mod.startswith(pkg + '.'):
                to_uncache.append(mod)
                break
    for mod in to_uncache:
        del sys.modules[mod]


def _is_hex_address(value) -> bool:
    """
    Checks if the given string of text type is an address in hexadecimal encoded form.
    """
    if not eth_utils.types.is_text(value):
        return False
    if not eth_utils.hexadecimal.is_hex(value):
        return False
    unprefixed = eth_utils.hexadecimal.remove_0x_prefix(value)
    return len(unprefixed) == 42


# pylint: disable=unused-argument
def _is_checksum_address(value) -> bool:
    return True


address.is_checksum_address = _is_checksum_address
address.is_hex_address = _is_hex_address
uncache(["eth_utils.address"])

AddressDecoder.value_bit_size = 21 * 8
