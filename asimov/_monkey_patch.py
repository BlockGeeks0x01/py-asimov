import sys
import eth_utils


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
    elif not eth_utils.hexadecimal.is_hex(value):
        return False
    else:
        unprefixed = eth_utils.hexadecimal.remove_0x_prefix(value)
        return len(unprefixed) == 42


def _is_checksum_address(value) -> bool:
    return True


from eth_utils import address
address.is_checksum_address = _is_checksum_address
address.is_hex_address = _is_hex_address
uncache(["eth_utils.address"])

from eth_abi.decoding import AddressDecoder
AddressDecoder.value_bit_size = 21 * 8

