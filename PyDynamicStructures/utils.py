import math
from collections import namedtuple
class MasterBuffer(object):
    def __init__(self, buf=None, off=0):
        self.buffer=buf
        self.offset=off

class MasterByte(object):
    def __init__(self, byte_val=None, off=0):
        self.byte_val=byte_val
        self.offset=off

class MasterValues(object):
    def __init__(self, val=None, off=None, bit_off=None):
        self.values=val
        self.offset=off
        self.bit_offset=bit_off


def sizeof(struct):
    return struct.size()

def get_variable(current_object, path):
    path = path.replace('\\', '/')
    split_path = path.split('/')
    start_object = current_object

    index = 0
    while split_path[index] in ('r', '.', '..'):
        if split_path[index] == 'r':
            start_object = current_object.root()
        elif split_path[index] == '..':
            start_object = start_object.get_parent()
        elif split_path[index] == '.':
            #start_object = start_object
            pass
        index += 1
    start_path = split_path[index:]

    try:
        this_dir = start_object
        for attr_name in start_path:
            this_dir = getattr(this_dir, attr_name)
    except AttributeError as e:
        raise AttributeError("Cannot find dir %s %s: message %s" % (attr_name, path, str(e)))
    return this_dir

def bit_size_in_bytes(size):
    return int(math.ceil(size/8.0))

def byte_to_int(char):
    if isinstance(char, int):
        return char
    return ord(char)

def int_to_byte(val):
    return chr(val)

def bytes_to_int(buffer, size, offset=0, lendian=True):
    buf_cut = buffer[offset:offset + size]
    if lendian:
        buf_cut = buf_cut[::-1]
    val = 0
    for b in buf_cut:
        val <<= 8
        val |= byte_to_int(b)
    return val

def bytes_to_bit(buffer, bit_size, struc_size_bytes=None,  bytes_offset=0, bit_offset=0, lendian=True):
    if struc_size_bytes is None:
        struc_size_bytes = bit_size_in_bytes(bit_offset + bit_size)
    val = bytes_to_int(buffer, struc_size_bytes, bytes_offset, lendian)
    mask = (1 << bit_size) - 1
    return (val >> bit_offset) & mask

def int_to_bits(val, size, offset=0):
    mask = (1 << size) - 1
    return (val >> offset) & mask

