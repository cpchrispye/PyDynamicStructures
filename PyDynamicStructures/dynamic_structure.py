from struct import unpack, pack, calcsize
from collections import Sequence, OrderedDict


def sizeof(struct):
    return struct.size()

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
        try:
            return pack(self.BASEENDIAN + self.BASEFORMAT, self.internal_value)
        except Exception as e:
            raise Exception("pack error class %s, value %s, message: %s" % (self.__class__.__name__, str(self.internal_value), str(e)))

    def unpack(self, buffer, offset=0):
        self.__offset = offset
        self.__buffer = buffer
        try:
            vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer[self.__offset:self.__offset + self.size()])
        except Exception as e:
            raise Exception("unpack error class %s, value %s, message: %s" % (self.__class__.__name__, str(self.internal_value), str(e)))

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


class DynObject(object):

    """
    DynObject will treat any (non)descriptor bound to its instance attributes as property
    this differs from object which only allows for descriptors to be associated to the class not the instance.
    effort has been made to not use __init__ so that any one inheriting does not need to super()
    """

    def __getattribute__(self, key):
        """
        If attribute has __get__ method call it and return result
        :param key:
        :return: value
        """
        v = object.__getattribute__(self, key)
        if hasattr(v, '__get__'):
            return v.__get__(self, type(self))
        return v

    def __setattr__(self, key, value):
        """

        :param key:
        :param value:
        :return:
        """
        if key not in self.__dict__:
            # if this is the first time set attribute to the what ever is passed
            object.__setattr__(self, key, value)
        else:
            # if attribute has __set__ we call its __set__ method unless the value we are setting has a __set__ method
            # then its likely that the user is trying to replace the descriptor. The user may wish to replace the
            # descriptor with another obect thats not a descriptor in which case the object should have a REPLACE attribute set to True
            v = self.__dict__[key]
            if (hasattr(v, '__set__')
                    and not (hasattr(value, '__set__')
                             or (hasattr(value, 'REPLACE') and value.REPLACE==True))):
                # set the property
                v.__set__(self, value)
            else:
                # set the attribute
                object.__setattr__(self, key, value)

    def get_attr_list_with(self, attr='__get__'):
        """
        gets a list of attributes with attribute
        :return: :class:`dict`
        """
        descriptors = {}
        for key, item in self.__dict__.items():
            if hasattr(item, attr):
                descriptors[key] = (item)
        return descriptors

class OrderedDynObject(DynObject):

    def __setattr__(self, key, value):
        if len(self.__dict__) == 0:
            self.__dict__['_fields'] = OrderedDict()
        if key not in self.__dict__['_fields']:
            self._fields[key] = None
        super(OrderedDynObject, self).__setattr__(key, value)

    def __getattr__(self, item):
        if len(self.__dict__) == 0:
            self.__dict__['_fields'] = OrderedDict()
        return super(OrderedDynObject, self).__getattribute__(item)

    def get_attr_list_with(self, attr='__get__'):
        """
        gets a list of attributes with attribute
        :return: :class:`dict`
        """
        descriptors = OrderedDict()
        for key in self.attributes():
            if key in self.__dict__ and hasattr(self.__dict__[key], attr):
                descriptors[key] = self.__dict__[key]
        return descriptors

    def attributes(self):
        return self._fields.keys()


class Structure(OrderedDynObject):
    """
    """
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
        for struct in self.get_attr_list_with('pack').values():
            byte_data += struct.pack()
        return byte_data

    def unpack(self, buffer, offset=0):
        index = 0
        self.__offset = offset
        self.__buffer = buffer
        for struct in self.get_attr_list_with('unpack').values():
            index += struct.unpack(buffer, index + offset)
        return index

    def update(self):
        index = 0
        for struct in self.get_attr_list_with('unpack').values():
            index += struct.unpack(self.__buffer, index + self.__offset)

    def size(self):
        size_in_bytes = 0
        for struct in self.get_attr_list_with('size').values():
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
                if index >= len(values):
                    break
                if hasattr(self.__getattribute__(key), 'set_values'):
                    index += self.__getattribute__(key).set_values(values[index:])
                else:
                    self.__setattr__(key, values[index])
                    index += 1
            return index

    def add_field(self, name, type_val, length=None):
        if isinstance(type(type_val), type):
            type_val = type_val()
        if length is None:
            self.__setattr__(name, type_val)
        elif length is not None:
            self.__setattr__(name, type_val * length)

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

    def update(self, from_buffer=True):
        if from_buffer:
            index = 0
            for struct in self:
                index += struct.unpack(self.__buffer, index + self.__offset)
        else:
            self.__buffer = bytes()
            for struct in self:
                self.__buffer += struct.pack()

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


class Selector(object):
    REPLACE  = True
    _fields_ = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.internal_state = None

    def select(self, **kwargs):
        raise Exception("select method needs defining")

    def __get__(self, instance, owner):
        return self.internal_state

    def __set__(self, instance, value):
        raise AttributeError("Cannot set Selector")

    def __delete__(self, instance):
        pass

    def pack(self):
        self.internal_state = self.select(**self.kwargs)
        return self.internal_state.pack()

    def unpack(self, buffer, offset=0):
        index = 0
        self.__offset = offset
        self.__buffer = buffer
        self.internal_state = self.select(**self.kwargs)
        index += self.internal_state.unpack(buffer, index + offset)
        return index



if __name__ == "__main__":

    class mySelect(Selector):

        def select(self, **kwargs):
            node = kwargs['length'].length
            return BYTE.__mul__(node)

    class sub(Structure):
        def __init__(self):
            self.a = UINT8()
            self.b = UINT32()


    class sub_alt(Structure):
        _fields_ = [
            ("c", UINT8),
            ("f", UINT16),
        ]


    class EncapsulationHeader(Structure):
        def __init__(self):
            self.command = UINT16()
            self.length = UINT8()
            self.session_handle = UINT32()
            self.status = UINT32()
            self.sender_context = UINT64()
            self.options = UINT32()
            self.data = mySelect(length=self)

    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    hd = EncapsulationHeader()

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




