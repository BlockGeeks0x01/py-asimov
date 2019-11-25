import eth_utils
import eth_abi.decoding


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


eth_utils.is_checksum_address = _is_checksum_address
eth_utils.is_hex_address = _is_hex_address
eth_utils.address.is_checksum_address = _is_checksum_address
eth_utils.address.is_hex_address = _is_hex_address
eth_abi.decoding.AddressDecoder.value_bit_size = 21 * 8

