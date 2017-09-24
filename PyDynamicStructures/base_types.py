import weakref
from struct import unpack, pack, calcsize
from PyDynamicStructures.dynamic_structure import StructureList
from PyDynamicStructures.descriptors import DynamicDescriptor

__all__ = [ 'BYTE', 'UINT8', 'UINT16', 'UINT32', 'UINT64', 'DOUBLE', 'FLOAT',
            'BYTE_L', 'UINT8_L', 'UINT16_L', 'UINT32_L', 'UINT64_L', 'DOUBLE_L', 'FLOAT_L',  'EMPTY', 'STRING', 'BaseType']

class BaseTypeError(Exception):
    def __init__(self, base_object, message):
        path = '.'.join([p.__class__.__name__ for p in base_object.get_path()])
        message = "object path = %s: message = %s" % (path, message)
        super(BaseTypeError, self).__init__(message)


class BaseType(DynamicDescriptor):
    BASEFORMAT   = ''
    BASEENDIAN   = '<'
    DEFAULTVALUE = 0
    REPLACE      = True

    def __init__(self, value=None):
        self.internal_value = self.DEFAULTVALUE
        if value is not None:
            self.internal_value = value

    def __dget__(self, instance, owner):
        return self.internal_value

    def __dset__(self, instance, value):
        self.internal_value = value

    def __ddelete__(self, instance):
        raise BaseTypeError(self, "Descriptor __delete__ not overridden correctly ")

    def set_parent(self, parent):
        self.__parent = weakref.ref(parent)

    def get_parent(self):
        try:
            return self.__parent()
        except AttributeError:
            return None

    def get_path(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.get_path() + [self]

    def set_values(self, val):
        if isinstance(val[0], (tuple, list, dict)):
            raise BaseTypeError(self, "values to be set are a sequence or dict need to be int or char")
        self.internal_value = val[0]
        return 1

    def pack(self):
        try:
            return pack(self.BASEENDIAN + self.BASEFORMAT, self.internal_value)
        except Exception as e:
            BaseTypeError(self, "pack error class %s, value %s, message: %s" % (str(self.internal_value), str(e)))

    def unpack(self, buffer, offset=0):
        self.__offset = offset
        self.__buffer = buffer
        try:
            vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer[self.__offset:self.__offset + self.size()])
        except Exception as e:

            BaseTypeError(self, "unpack error class %s, value %s, message: %s" % (str(self.internal_value), str(e)))

        self.internal_value = vals[0]

        return self.size()

    def update(self):
        vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer[self.__offset:self.__offset + self.size()])
        self.internal_value = vals[0]

    def update_selectors(self):
        pass

    @classmethod
    def get_format(cls):
        return [cls.BASEFORMAT]

    @classmethod
    def size(cls):
        return calcsize(cls.BASEENDIAN + cls.BASEFORMAT)

    def __str__(self):
        return str(self.internal_value)

    def __repr__(self):
        return self.__class__.__name__ + ": " + str(self.internal_value)

    @classmethod
    def __mul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])

    @classmethod
    def __rmul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])


class EMPTY(BaseType):
    BASEFORMAT = ''

    def __dget__(self, instance, owner):
        return None

    def __dset__(self, instance, value):
        pass

    def set_values(self, val):
        return 0

    def unpack(self, buffer, offset=0):
        return 0

    def pack(self):
        return bytes()


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

