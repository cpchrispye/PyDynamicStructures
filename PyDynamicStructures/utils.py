import math

def bit_size_in_bytes(size):
    return int(math.ceil(size//8))

def byte_to_int(char):
    if isinstance(char, int):
        return char
    return ord(char)

def bytes_to_int(buffer, size, offset=0, lendian=True):
    buf_cut = buffer[offset:offset + size]
    if not lendian:
        buf_cut = buf_cut[::-1]
    val = 0
    for b in buf_cut:
        val <<= 8
        val |= byte_to_int(b)
    return val

def bytes_to_bit(buffer, bit_size,  bytes_offset=0, bit_offset=0, lendian=True):
    span = bit_size_in_bytes(bit_offset + bit_size)
    val = bytes_to_int(buffer, span, bytes_offset, lendian)
    mask = (1 << bit_size) - 1
    return (val >> bit_offset) & mask