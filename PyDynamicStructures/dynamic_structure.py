from PyDynamicStructures.base_types import *
from collections import Sequence, OrderedDict
import weakref

__all__ = ['Structure', 'StructureList', 'Selector', 'sizeof']

SETTER = '__dset__'
GETTER = '__dget__'

def sizeof(struct):
    return struct.size()

def get_descriptor(key, self, getter, supered_method):
    v = supered_method(key)
    if hasattr(v, getter):
        return getattr(v, getter)(self, type(self))
    return v

def set_descriptor(key, value, self, setter, supered_method, order=False):
    if order:
        try:
            self._fields[key] = None
        except Exception:
            object.__setattr__(self, '_fields', OrderedDict())
            self._fields[key] = None

    try:
        v = self.get_item(key)
    except Exception:
        if hasattr(value, 'set_parent'):
            value.set_parent(self)
        return supered_method(key, value)

    # if attribute has __set__ we call its __set__ method unless the value we are setting has a __set__ method
    # then its likely that the user is trying to replace the descriptor. The user may wish to replace the
    # descriptor with another object thats not a descriptor in which case the object should have a REPLACE attribute set to True
    if (hasattr(v, setter)
        and not (hasattr(value, setter)
                 or (hasattr(value, 'REPLACE') and value.REPLACE == True))):
        # set the property
        getattr(v, setter)(self, value)
    else:
        # set the attribute
        return supered_method(key, value)


class StructureBase(object):

    def get_structure_items(self, with_attr=None):
        print("not here")
        raise Exception("get_structure_items needs defining")

    def get_item(self, key):
        raise Exception("get_items needs defining")

    def set_item(self, key, value):
        raise Exception("get_items needs defining")

    def get_attributes(self):
        raise Exception("get_items needs defining")

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

    def get_format(self):
        out = []
        for struct in self.get_structure_items().values():
            out += struct.get_format()
        return out

    def get_structure_items(self, with_attr=None):
        with_attr = 'pack' if with_attr is None else with_attr
        out = OrderedDict()
        for name in self.get_attributes():
            value = self.get_item(name)
            if hasattr(value, with_attr):
                out[name] = value
        return out

    def set_values(self, value):
        index = 0
        for k, v in self.get_structure_items('set_values').items():
            if index >= len(value):
                break
            key = index
            if isinstance(value, dict):
                key = k

            if isinstance(value[key], (Sequence, dict)):
                v.set_values(value[key])
                index += 1
            else:
                index += v.set_values(value[key:])
        return index

    def __mul__(self, other):
        return StructureList([self() for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([self() for _ in range(int(other))])


class Structure(StructureBase):
    """
    """
    REPLACE  = True
    _fields_ = []

    def __new__(cls, *args, **kwargs):
        new_instance = super(Structure, cls).__new__(cls)
        new_instance.add_fields(cls._fields_)
        return new_instance

    @classmethod
    def build_with_values(cls, *args, **kwargs):
        new_instance = cls()
        values = list(args)
        if len(values) == 0:
            values = dict(kwargs)
        if len(values):
            new_instance.set_values(values)
        return new_instance

    def get_item(self, key):
        return object.__getattribute__(self, key)

    def __getattribute__(self, key):
        return get_descriptor(key, self, GETTER, super(Structure, self).__getattribute__)

    def set_item(self, key, value):
        object.__setattr__(self, key, value)

    def __setattr__(self, key, value):
        set_descriptor(key, value, self, SETTER, super(Structure, self).__setattr__, True)

    def get_attributes(self):
        return self._fields.keys()

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


class StructureList(list, StructureBase):
    REPLACE = True

    def get_item(self, key):
        return list.__getitem__(self, key)

    def __getitem__(self, key):
        return get_descriptor(key, self,  GETTER, super(StructureList, self).__getitem__)

    def set_item(self, key, value):
        list.__setitem__(self, key, value)

    def __setitem__(self, key, value):
        set_descriptor(key, value, self, SETTER, super(StructureList, self).__setitem__)

    def get_attributes(self):
        return range(len(self))



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

    def set_values(self, values):
        self.update_selectors()
        return self.internal_state.set_values(values)

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

    def get_format(self):
        out = []
        for struct in self.internal_state.get_structure_items().values():
            out += struct.get_format()
        return out

if __name__ == "__main__":

    class DynamicArray(Selector):

        def select(self, **kwargs):
            size     = self.get_variable(kwargs['length'])
            str_type = kwargs['type']()
            return str_type * size

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
            self.data = DynamicArray(length='length', type=UINT8)

    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    hd = EncapsulationHeader.build_with_values(0,5,2,3,4,5,6,7,8,9,10,11,12,13,14)

    hd.unpack(header_data)
    v = hd.command
    d = hd.pack()
    print(d.encode('hex'))
    print(data)
    alt_struct = sub_alt(3, 5)
    hd.options = alt_struct
    hd.update()
    hd.length = 10
    hd.update_selectors()
    print(hd.get_format())
    hd.options.f = 0
    d = hd.pack()
    print(data)
    print(d.encode("hex"))

    i=1




