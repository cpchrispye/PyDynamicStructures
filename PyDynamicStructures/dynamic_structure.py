from struct import unpack, pack, calcsize
from collections import Sequence, Iterable, OrderedDict
from abc import ABCMeta


def sizeof(struct):
    return struct.size()

def flatten(items):
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield flatten(x)
        else:
            yield x

class BaseType(object):
    BASEFORMAT   = ''
    BASEENDIAN   = '<'
    DEFAULTVALUE = 0
    REPLACE      = True

    def __init__(self, value=None):
        self.internal_value = self.DEFAULTVALUE
        if value is not None:
            self.internal_value = value

    def __get__(self, instance, owner):
        return self.internal_value

    def __set__(self, instance, value):
        self.internal_value = value

    def __delete__(self, instance):
        raise AttributeError("Descriptor __delete__ not overridden correctly " + self.__class__.__name__)

    def pack(self):
        return pack(self.BASEENDIAN + self.BASEFORMAT, self.internal_value)

    def unpack(self, buffer, offset=0):
        self.__offset = offset
        self.__buffer = buffer

        vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer[self.__offset:self.__offset + self.size()])

        self.internal_value = vals[0]

        return self.size()

    def update(self):
        vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer[self.__offset:self.__offset + self.size()])
        self.internal_value = vals[0]

    @classmethod
    def get_format(cls):
        return [cls.BASEFORMAT]

    @classmethod
    def size(cls):
        return calcsize(cls.BASEENDIAN + cls.BASEFORMAT)

    def __str__(self):
        return str(self.internal_value)

    def __repr__(self):
        return self.__class__.__name__ + ": " +  str(self.internal_value)

    @classmethod
    def __mul__(cls, other):
        return StructureList([cls() for _  in range(int(other))])

    @classmethod
    def __rmul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])

class EMPTY(BaseType):
    BASEFORMAT = ''

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

class Descriptor():
    __metaclass__ = ABCMeta
    REPLACE = True

    def __get__(self, instance, owner):
        raise AttributeError("Descriptor not overridden correctly " + self.__class__.__name__)

    def __set__(self, instance, value):
        raise AttributeError("Descriptor not overridden correctly " + self.__class__.__name__)

    def __delete__(self, instance):
        raise AttributeError("Descriptor not overridden correctly " + self.__class__.__name__)

class DynObject(object):

    def __getattribute__(self, key):
        "Emulate type_getattro() in Objects/typeobject.c"
        v = object.__getattribute__(self, key)
        if hasattr(v, '__get__'):
            return v.__get__(self, type(self))
        return v

    def __setattr__(self, key, value):
        if key not in self.__dict__:
            # if this is the first time set attribute to the what ever is passed
            object.__setattr__(self, key, value)
        else:
            v = self.__dict__[key]
            if (hasattr(v, '__set__')
                    and not (hasattr(value, '__set__')
                             or (hasattr(value, 'REPLACE') and value.REPLACE==True))):
                # set the property
                v.__set__(self, value)
            else:
                # set the attribute
                object.__setattr__(self, key, value)

    def get_descriptors(self):
        descriptors = {}
        for key, item in self.__dict__.items():
            if hasattr(item, '__get__'):
                descriptors[key] = (item)
        return descriptors

class OrderedDynObject(DynObject):

    def __setattr__(self, key, value):
        if len(self.__dict__) == 0:
            self.__dict__['_fields'] = OrderedDict()
        if key not in self.__dict__['_fields']:
            self._fields[key] = None
        super(OrderedDynObject, self).__setattr__(key, value)

    def get_descriptors(self, attr='__get__'):
        descriptors = OrderedDict()
        for key in self.attributes():
            if hasattr(self.__dict__[key], attr):
                descriptors[key] = self.__dict__[key]
        return descriptors

    def attributes(self):
        return self._fields.keys()


class Structure(OrderedDynObject):
    REPLACE  = True
    _fields_ = []

    def __new__(cls, *args, **kwargs):
        new_instance = super(Structure, cls).__new__(cls)
        new_instance.add_fields(cls._fields_)
        values = list(args)
        if len(values) == 0:
            values = dict(kwargs)
        if len(values):
            new_instance.set_values(values)
        return new_instance

    def pack(self):
        byte_data = bytes()
        for struct in self.get_descriptors('pack').values():
            byte_data += struct.pack()
        return byte_data

    def unpack(self, buffer, offset=0):
        index = 0
        self.__offset = offset
        self.__buffer = buffer
        for struct in self.get_descriptors('unpack').values():
            index += struct.unpack(buffer, index + offset)
        return index

    def update(self):
        index = 0
        for struct in self.get_descriptors('unpack').values():
            index += struct.unpack(self.__buffer, index + self.__offset)

    def size(self):
        size_in_bytes = 0
        for struct in self.get_descriptors('size').values():
            size_in_bytes += struct.size()
        return size_in_bytes

    def set_values(self, values):
        if isinstance(values, dict):
            for key, val in values.items():
                if hasattr(self.__getattribute__(key), 'set_values'):
                    self.__getattribute__(key).set_values(val)
                else:
                    self.__setattr__(key, val)
        elif isinstance(values, Sequence):
            index = 0
            for key in self.attributes():
                if hasattr(self.__getattribute__(key), 'set_values'):
                    index += self.__getattribute__(key).set_values(values[index:])
                else:
                    self.__setattr__(key, values[index])
                    index += 1
            return index

    def add_field(self, name, type, length=None):
        if length is None:
            self.__setattr__(name, type())
        elif length is not None:
            self.__setattr__(name, type() * length)

    def add_fields(self, fields):
        for field in fields:
            if len(field) == 3:
                name, type, length = field
            elif len(field) == 2:
                name, type = field
                length = None
            else:
                raise Exception("_fields_ takes 2 or 3 colomns")
            self.add_field(name, type, length)

    def get(self, name=None):
        out = OrderedDict()
        for n in self.attributes():
            out[n] = self.__dict__[n]
        if name is not None:
            return out[name]
        return out

    @classmethod
    def __mul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])

    @classmethod
    def __rmul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])


class StructureList(list):
    REPLACE = True

    def pack(self):
        byte_data = bytes()
        for struct in self:
            byte_data += struct.pack()
        return byte_data

    def unpack(self, buffer, offset=0):
        index = 0
        self.__offset = offset
        self.__buffer = buffer
        for struct in self:
            index += struct.unpack(buffer, index + offset)
        return index

    def update(self):
        index = 0
        for struct in self:
            index += struct.unpack(self.__buffer, index + self.__offset)

    def size(self):
        size_in_bytes = 0
        for struct in self:
            size_in_bytes += struct.size()
        return size_in_bytes

    @classmethod
    def __mul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])

    @classmethod
    def __rmul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])


if __name__ == "__main__":

    class sub(Structure):
        def __init__(self):
            self.a = UINT8()
            self.b = UINT32()


    class sub_alt(Structure):
        _fields_ = [
            ("c", UINT8),
            ("f", UINT16),
        ]


    class EnipHeader(Structure):
        _fields_ = [
            ("command", UINT16),
            ("length", UINT16),
            ("session_handle", UINT32),
            ("status", UINT32),
            ("sender_context", UINT64),
            ("options", UINT32),
            ("data", sub, 10),
        ]

    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    hd = EnipHeader()

    hd.unpack(header_data)
    d = hd.pack()
    alt_struct = sub_alt(3, 5)
    hd.options = alt_struct
    hd.update()
    print(hd.options.pack().encode("hex"))
    print(data)
    print(d.encode("hex"))
    print(hd.data[5].a)
    i=1




