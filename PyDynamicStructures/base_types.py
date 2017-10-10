from PyDynamicStructures.dynamic_structure import VirtualStructure, StructureList
from PyDynamicStructures.descriptors import DescriptorItem
from PyDynamicStructures.utils import MasterValues, MasterBuffer, bytes_to_bit
from struct import pack, unpack, calcsize
from collections import OrderedDict

__all__ = [ 'BYTE', 'UINT8', 'UINT16', 'UINT32', 'UINT64', 'DOUBLE', 'FLOAT',
            'BYTE_L', 'UINT8_L', 'UINT16_L', 'UINT32_L', 'UINT64_L', 'DOUBLE_L', 'FLOAT_L',  'EMPTY', 'STRING', 'BaseType', ]#'BitField']

class BaseTypeError(Exception):
    def __init__(self, base_object, message):
        path = '.'.join([p.__class__.__name__ for p in base_object.get_parents()])
        message = "object path = %s: message = %s" % (path, message)
        super(BaseTypeError, self).__init__(message)

class BaseType(VirtualStructure, DescriptorItem):
    __slots__    = ('internal_value', 'buffer', 'buffer_offset', 'parent')
    BASEFORMAT   = None
    DEFAULTVALUE = 0
    BASEENDIAN   = '<'

    @classmethod
    def from_values(cls, val):
        ins = cls(val)
        return ins

    def __init__(self, value=None):
        self.internal_value = value
        if self.internal_value is None:
            self.internal_value = self.DEFAULTVALUE

    def _getter_(self, instance):
        return self.internal_value

    def _setter_(self, instance, value):
        self.internal_value = value

    @property
    def structured_values(self):
        return self.internal_value

    def _pack(self):
        try:
            return pack(self.BASEENDIAN + self.BASEFORMAT, self.internal_value)
        except Exception as e:
            raise BaseTypeError(self, "pack error class %s, value %s, message: %s" % (str(self.internal_value), str(e)))

    def _unpack(self, key, buffer=None):
        if buffer is not None:
            if not isinstance(buffer, MasterBuffer):
                buffer = MasterBuffer(buffer, 0)
            self.buffer = buffer
            self.buffer_offset = self.buffer.offset
        else:
            self.buffer.offset = self.buffer_offset

        try:
            size = self.size()
            vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.buffer.buffer[self.buffer.offset:self.buffer.offset + size])
        except Exception as e:
            raise BaseTypeError(self, "unpack error class %s, value %s, message: %s" % (str(self.internal_value), str(e)))

        self.internal_value = vals[0]
        self.buffer.offset += size
        return size

    def _rebuild(self, key):
        pass

    def _set_values(self, key, value_wrapper):
        if isinstance(value_wrapper, MasterValues):
            self.internal_value = value_wrapper.values[value_wrapper.offset]
            value_wrapper.offset += 1
        elif isinstance(value_wrapper, (dict, OrderedDict)):
            if key in value_wrapper:
                self.internal_value = value_wrapper[key]

    def set_parent(self, parent):
        self.parent = parent

    def get_parent(self):
        return self.parent

    def root(self):
        return self.get_parents()[0]

    def get_parents(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.get_parents() + [self]

    def size(self):
        return calcsize(self.BASEFORMAT)

    @property
    def hex(self):
        return self._pack().encode('hex')

    def __mul__(self, other):
        return StructureList([type(self).from_values(self.internal_value) for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([type(self).from_values(self.internal_value) for _ in range(int(other))])

    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__, str(self.internal_value))

    def __str__(self):
        return str(self.internal_value)

class EMPTY(BaseType):
    BASEFORMAT = ''
    DEFAULTVALUE = None

    def _getter_(self, instance):
        return None

    def _setter_(self, instance, value):
        pass

    def _pack(self):
        pass

    def _unpack(self, key, value, buffer_wrapper):
        pass

    def _set_values(self, key, value, value_wrapper):
        pass


    def size(self):
        return 0


class BigEndian(BaseType):
    __slots__ = ()
    BASEENDIAN = '>'


class LittleEndian(BaseType):
    __slots__ = ()
    BASEENDIAN = '<'


class BYTE(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'c'
    DEFAULTVALUE = '\0'

    def __repr__(self):
        return self.__class__.__name__ + ": 0x" +  self.internal_value.encode("hex")


class UINT8(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'B'


class UINT16(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'H'


class UINT32(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'I'


class UINT64(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'Q'


class INT8(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'b'


class INT16(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'h'


class INT32(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'i'


class INT64(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'q'


class FLOAT(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'f'


class DOUBLE(BigEndian):
    __slots__ = ()
    BASEFORMAT = 'd'


class STRING(BigEndian):
    __slots__ = ()
    BASEFORMAT = 's'


class BYTE_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'c'
    DEFAULTVALUE = '\0'


class UINT8_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'B'


class UINT16_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'H'


class UINT32_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'I'


class UINT64_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'Q'


class INT8_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'b'


class INT16_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'h'


class INT32_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'i'


class INT64_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'q'


class FLOAT_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'f'


class DOUBLE_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 'd'


class STRING_L(LittleEndian):
    __slots__ = ()
    BASEFORMAT = 's'


class BitElement(BaseType):
    def __init__(self, bit_size):
        self.internal_value = self.DEFAULTVALUE
        self.bit_size       = bit_size

    @property
    def structured_values(self):
        return self.internal_value

    def _pack(self):
        mask = (0x01 << self.bit_size + 1) - 1
        return self.internal_value & mask

    def _unpack(self, key, buffer=None):
        if buffer is not None:
            if not isinstance(buffer, MasterBuffer):
                buffer = MasterBuffer(buffer, 0, 0)
            self.buffer = buffer
            self.buffer_offset = self.buffer.offset
            self.buffer_bit_offset = self.buffer.bit_offset
        else:
            self.buffer.offset = self.buffer_offset
            self.buffer.bit_offset = self.buffer_bit_offset

        try:
            parent = self.get_parent()
            size = self.size()
            vals = bytes_to_bit(self.buffer.buffer, size, parent.size(), self.buffer.offset, self.buffer.bit_offset, parent.LENDIAN)
        except Exception as e:
            raise BaseTypeError(self, "unpack error, message: %s" % (str(e)))

        self.internal_value = vals
        self.buffer.bit_offset += size
        return size

    def size(self):
        return self.bit_size

    def _rebuild(self, key):
        pass

    def _set_values(self, key, value_wrapper):
        if isinstance(value_wrapper, MasterValues):
            self.internal_value = value_wrapper.values[value_wrapper.offset]
            value_wrapper.offset += 1
        elif isinstance(value_wrapper, (dict, OrderedDict)):
            if key in value_wrapper:
                self.internal_value = value_wrapper[key]

    # def __mul__(self, other):
    #     return StructureList([type(self).from_values(self.internal_value) for _ in range(int(other))])
    #
    # def __rmul__(self, other):
    #     return StructureList([type(self).from_values(self.internal_value) for _ in range(int(other))])

    def __repr__(self):
        return '%s: %b' % (self.__class__.__name__, self.internal_value)

    def __str__(self):
        return str(self.internal_value)