from PyDynamicStructures.byte_structure import VirtualStructure, StructureList
from PyDynamicStructures.meta import MetaItem
from PyDynamicStructures.utils import MasterValues, MasterBuffer
from struct import pack, unpack, calcsize

__all__ = [ 'BYTE', 'UINT8', 'UINT16', 'UINT32', 'UINT64', 'DOUBLE', 'FLOAT',
            'BYTE_L', 'UINT8_L', 'UINT16_L', 'UINT32_L', 'UINT64_L', 'DOUBLE_L', 'FLOAT_L',  'EMPTY', 'STRING', 'BaseType', 'BitField']

class BaseTypeError(Exception):
    def __init__(self, base_object, message):
        path = '.'.join([p.__class__.__name__ for p in base_object.path()])
        message = "object path = %s: message = %s" % (path, message)
        super(BaseTypeError, self).__init__(message)

class BaseType(VirtualStructure, MetaItem):
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

    def _unpack(self, buffer=None):
        if buffer is not None:
            if not isinstance(buffer, MasterBuffer):
                buffer = MasterBuffer(buffer, 0)
            self.__buffer = buffer
            self.__buffer_offset = self.__buffer.offset
        else:
            self.__buffer.offset = self.__buffer_offset

        try:
            size = self.size()
            vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer.buffer[self.__buffer.offset:self.__buffer.offset + size])
        except Exception as e:
            raise BaseTypeError(self, "unpack error class %s, value %s, message: %s" % (str(self.internal_value), str(e)))

        self.internal_value = vals[0]
        self.__buffer.offset += size
        return size

    def refresh(self):
        pass

    def _rebuild(self, key, value):
        pass

    def set_values(self, value_wrapper):
        m_val = value_wrapper
        if isinstance(m_val, MasterValues):
            m_val = m_val.values[m_val.offset]
            m_val.offset += 1
        self.internal_value = m_val
        return 1

    def _set_values(self, key, value, value_wrapper):
        m_val = value
        if isinstance(m_val, MasterValues):
            m_val = m_val.values[m_val.offset]
            m_val.offset += 1
        self.internal_value = m_val
        return 1

    def set_parent(self, parent):
        self.__parent = parent

    def size(self):
        return [calcsize(self.BASEFORMAT)]

    def __mul__(self, other):
        return StructureList([type(self).from_values(self.internal_value) for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([type(self).from_values(self.internal_value) for _ in range(int(other))])

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
    BASEENDIAN = '>'


class LittleEndian(BaseType):
    BASEENDIAN = '<'


class BYTE(BigEndian):
    BASEFORMAT = 'c'
    DEFAULTVALUE = '\0'

    def __repr__(self):
        return self.__class__.__name__ + ": 0x" +  self.internal_value.encode("hex")


class UINT8(BigEndian):
    BASEFORMAT = 'B'


class UINT16(BigEndian):
    BASEFORMAT = 'H'


class UINT32(BigEndian):
    BASEFORMAT = 'I'


class UINT64(BigEndian):
    BASEFORMAT = 'Q'


class INT8(BigEndian):
    BASEFORMAT = 'b'


class INT16(BigEndian):
    BASEFORMAT = 'h'


class INT32(BigEndian):
    BASEFORMAT = 'i'


class INT64(BigEndian):
    BASEFORMAT = 'q'


class FLOAT(BigEndian):
    BASEFORMAT = 'f'


class DOUBLE(BigEndian):
    BASEFORMAT = 'd'


class STRING(BigEndian):
    BASEFORMAT = 's'


class BYTE_L(LittleEndian):
    BASEFORMAT = 'c'
    DEFAULTVALUE = '\0'


class UINT8_L(LittleEndian):
    BASEFORMAT = 'B'


class UINT16_L(LittleEndian):
    BASEFORMAT = 'H'


class UINT32_L(LittleEndian):
    BASEFORMAT = 'I'


class UINT64_L(LittleEndian):
    BASEFORMAT = 'Q'


class INT8_L(LittleEndian):
    BASEFORMAT = 'b'


class INT16_L(LittleEndian):
    BASEFORMAT = 'h'


class INT32_L(LittleEndian):
    BASEFORMAT = 'i'


class INT64_L(LittleEndian):
    BASEFORMAT = 'q'


class FLOAT_L(LittleEndian):
    BASEFORMAT = 'f'


class DOUBLE_L(LittleEndian):
    BASEFORMAT = 'd'


class STRING_L(LittleEndian):
    BASEFORMAT = 's'
