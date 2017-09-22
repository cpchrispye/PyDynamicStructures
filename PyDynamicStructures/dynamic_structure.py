from struct import unpack, pack, calcsize
from collections import Sequence, OrderedDict
import weakref

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

    def __dget__(self, instance, owner):
        return self.internal_value

    def __dset__(self, instance, value):
        self.internal_value = value

    def __ddelete__(self, instance):
        raise AttributeError("Descriptor __delete__ not overridden correctly " + self.__class__.__name__)

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

    def pack(self):
        try:
            return pack(self.BASEENDIAN + self.BASEFORMAT, self.internal_value)
        except Exception as e:
            path = '.'.join([p.__class__.__name__ for p in self.get_path()])
            raise Exception("pack error class %s, value %s, message: %s" % (path, str(self.internal_value), str(e)))

    def unpack(self, buffer, offset=0):
        self.__offset = offset
        self.__buffer = buffer
        try:
            vals = unpack(self.BASEENDIAN + self.BASEFORMAT, self.__buffer[self.__offset:self.__offset + self.size()])
        except Exception as e:
            path = '.'.join([p.__class__.__name__ for p in self.get_path()])
            raise Exception("unpack error class %s, value %s, message: %s" % (path, str(self.internal_value), str(e)))

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


class DescriptorObject(object):

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
        getter = '__dget__'
        v = object.__getattribute__(self, key)
        if hasattr(v, getter):
            return getattr(v, getter)(self, type(self))
        return v

    def __setattr__(self, key, value):
        """

        :param key:
        :param value:
        :return:
        """
        setter = '__dset__'
        try:
            v = self.__dict__[key]
        except KeyError:
            object.__setattr__(self, key, value)
            return None

        # if attribute has __set__ we call its __set__ method unless the value we are setting has a __set__ method
        # then its likely that the user is trying to replace the descriptor. The user may wish to replace the
        # descriptor with another obect thats not a descriptor in which case the object should have a REPLACE attribute set to True
        if (hasattr(v, setter)
            and not (hasattr(value, setter)
                     or (hasattr(value, 'REPLACE') and value.REPLACE == True))):
            # set the property
            getattr(v, setter)(self, value)
        else:
            # set the attribute
            object.__setattr__(self, key, value)


class DescriptorList(list):
    REPLACE = True

    def __getitem__(self, key):
        """
        :param key:
        :return: value
        """
        getter = '__dget__'
        v = list.__getitem__(self, key)
        if hasattr(v, getter):
            return getattr(v, getter)(self, type(self))
        return v

    def __setitem__(self, key, value):
        """
        :param key:
        :param value:
        :return:
        """
        setter = '__dset__'
        try:
            v = list.__getitem__(self, key)
        except KeyError:
            return super(list, self).__setitem__(key, value)

        # if attribute has __set__ we call its __set__ method unless the value we are setting has a __set__ method
        # then its likely that the user is trying to replace the descriptor. The user may wish to replace the
        # descriptor with another object thats not a descriptor in which case the object should have a REPLACE attribute set to True
        if (hasattr(v, setter)
            and not (hasattr(value, setter)
                     or (hasattr(value, 'REPLACE') and value.REPLACE == True))):
            # set the property
            setattr(v, setter, value)
        else:
            # set the attribute
            return super(list, self).__setitem__(key, value)


class OrderedDescriptorObject(DescriptorObject):

    def __setattr__(self, key, value):
        try:
            fields = self.__dict__['_fields']
        except KeyError:
            fields = OrderedDict()
            self.__dict__['_fields'] = fields

        if key not in fields:
            fields[key] = None
        super(OrderedDescriptorObject, self).__setattr__(key, value)

    def __getattr__(self, item):
        if item == '_fields':
            fields = OrderedDict()
            self.__dict__['_fields'] = fields
            return fields
        return super(OrderedDescriptorObject, self).__getattribute__(item)

    def attributes(self):
        return self._fields.keys()


def get_dict_attr(obj, attr):
    for obj in [obj] + obj.__class__.mro():
        if attr in obj.__dict__:
            return obj.__dict__[attr]
    raise AttributeError


def get_attributes_with(ordered_dyn_object, has_attribute):
    out = OrderedDict()
    for attr_name in ordered_dyn_object.attributes():
        attr = get_dict_attr(ordered_dyn_object, attr_name)
        if hasattr(attr, has_attribute):
            out[attr_name] = attr
    return out


class StructureBase(OrderedDescriptorObject):

    def get_structure_items(self, with_attr=None):
        raise Exception("get_structure_items ned defining")

    def set_parent(self, parent):
        self._parent = weakref.ref(parent)

    def get_parent(self):
        try:
            return self._parent()
        except AttributeError:
            return None

    def get_path(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.get_path() + [self]

    def update(self):
        index = 0
        for struct in self.get_structure_items('unpack').values():
            index += struct.unpack(self._buffer, index + self._offset)

    def update_selectors(self):
        for struct in self.get_structure_items('update_selectors').values():
            struct.update_selectors()

    def pack(self):
        byte_data = bytes()
        for struct in self.get_structure_items('pack').values():
            byte_data += struct.pack()
        return byte_data

    def unpack(self, buffer, offset=0):
        index = 0
        self._offset = offset
        self._buffer = buffer
        for struct in self.get_structure_items('unpack').values():
            index += struct.unpack(buffer, index + offset)
        return index

    def size(self):
        size_in_bytes = 0
        for struct in self.get_structure_items('size').values():
            size_in_bytes += struct.size()
        return size_in_bytes

    @classmethod
    def __mul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])

    @classmethod
    def __rmul__(cls, other):
        return StructureList([cls() for _ in range(int(other))])


class Structure(StructureBase):
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

    def __setattr__(self, key, value):
        super(Structure, self).__setattr__(key, value)
        if hasattr(value, 'set_parent') and key != '_parent':
            value.set_parent(self)

    def get_structure_items(self, with_attr=None):
        with_attr =  'pack' if with_attr is None else with_attr
        return get_attributes_with(self, with_attr)

    def set_values(self, values):
        if isinstance(values, dict):
            for key, val in values.items():
                attr = getattr(self, key)
                if hasattr(attr, 'set_values'):
                    attr.set_values(val)
                else:
                    setattr(self, key, val)

        elif isinstance(values, Sequence):
            index = 0
            for key in self.attributes():
                if index >= len(values):
                    break
                attr = getattr(self, key)
                if hasattr(attr, 'set_values'):
                    index += attr.set_values(values[index:])
                else:
                    setattr(self, key, values[index])
                    index += 1
            return index

    def add_field(self, name, type_val, length=None):
        if isinstance(type(type_val), type):
            type_val = type_val()

        if length is None:
            setattr(self, name, type_val)
        elif length is not None:
            setattr(self, name, type_val * length)

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


class StructureList(DescriptorList, StructureBase):
    REPLACE = True

    def __setitem__(self, key, value):
        super(Structure, self).__setitem__(key, value)
        if hasattr(value, 'set_parent'):
            value.set_parent(self)

    def get_structure_items(self, with_attr=None):
        with_attr = 'pack' if with_attr is None else with_attr
        return OrderedDict([(k, val) for k, val in enumerate(self) if hasattr(val, with_attr)])


class Selector(StructureBase):
    REPLACE  = True
    _fields_ = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.internal_state = None

    def select(self, **kwargs):
        raise Exception("select method needs defining")

    def __dget__(self, instance, owner):
        return self.internal_state

    def __dset__(self, instance, value):
        raise AttributeError("Cannot set Selector")

    def __ddelete__(self, instance):
        pass

    def get_structure_items(self, with_attr=None):
        raise Exception(".get_structure_items() called on Selector this should not occur")

    def get_variable(self, path):
        if path[0] == '.':
            path = path[1:]
        attr_names = path.split('.')
        root = self.get_path()[0]
        try:
            this_dir = root
            for attr_name in attr_names:
                this_dir = getattr(this_dir, attr_name)
        except AttributeError as e:
            raise AttributeError("Cannot find dir %s %s: message %s" % (attr_name, path, str(e)))
        return this_dir

    def update(self):
        if self.internal_state is None:
            raise Exception("Selector needs to be initialized call unpack() on it")
        return self.internal_state.update(self._buffer)

    def update_selectors(self):
        self.internal_state = self.select(**self.kwargs)

    def pack(self):
        if self.internal_state is None:
            raise Exception("Selector needs to be initialized call unpack() on it")
        return self.internal_state.pack()

    def unpack(self, buffer, offset=0):
        index = 0
        self._offset = offset
        self._buffer = buffer
        self.internal_state = self.select(**self.kwargs)
        index += self.internal_state.unpack(buffer, index + offset)
        return index



if __name__ == "__main__":

    class DynamicArray(Selector):

        def select(self, **kwargs):
            size     = self.get_variable(kwargs['length'])
            str_type = kwargs['type']
            return str_type.__mul__(size)

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
            self.data = DynamicArray(length='.length', type=UINT8 )

    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    hd = EncapsulationHeader()

    hd.unpack(header_data)
    d = hd.pack()
    print(d.encode('hex'))
    print(data)
    alt_struct = sub_alt(3, 5)
    hd.options = alt_struct
    hd.update()
    hd.length = 10
    hd.update_selectors()
    print(hd.options.pack().encode("hex"))
    hd.options.f = 0
    d = hd.pack()
    print(data)
    print(d.encode("hex"))

    i=1




