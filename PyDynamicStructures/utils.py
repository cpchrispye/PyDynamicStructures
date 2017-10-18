import math
from collections import namedtuple, OrderedDict
import struct

class MasterBuffer(object):
    def __init__(self, buf=None, off=0):
        self.buffer=buf
        self.offset=off


class MasterByte(object):
    def __init__(self, byte_val=None, off=0, bit_size=None, low_first=True):
        self.byte_val=byte_val
        self.offset=off
        self.low_first = low_first
        self.bit_size = bit_size

class MasterValues(object):
    def __init__(self, val=None, off=0):
        self.values=val
        self.offset=off

def get_values(key, values, base_type=False):
    if values is None:
        return None
    if isinstance(values, MasterValues):
        if values.offset >= len(values.values):
            return None
        output = values.values[values.offset]
        # base types can only take a single value no lists allowed
        if base_type:
            if isinstance(output, (list, tuple)):
                raise Exception('base types cannot take list or tuple')
            values.offset += 1
            return output
        else:
            #structure types can take nested sequences
            if isinstance(output, (list, tuple)):
                values.offset += 1
                return MasterValues(output, 0)
            else:# otherwise send on master values un touched
                return values
    elif isinstance(values, (dict, OrderedDict)):
        return values.get(key, None)

    raise Exception('Set values error attribute %s invalid type %s' %(str(key), type(values).__name__()))


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
        return None #raise AttributeError("Cannot find dir %s %s: message %s" % (attr_name, path, str(e)))
    return this_dir

def bit_size_in_bytes(size):
    return int(math.ceil(size/8.0))

def byte_to_int(char):
    if isinstance(char, int):
        return char
    return ord(char)

def int_to_byte(val):
    return struct.pack("B", val)

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

