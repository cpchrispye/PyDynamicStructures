from PyDynamicStructures.base_types import *
from PyDynamicStructures.descriptors import DynamicDescriptor, ClassDesc, ListDesc
from collections import Sequence, OrderedDict
import weakref

__all__ = ['Structure', 'StructureList', 'Selector', 'sizeof']

def sizeof(struct):
    return struct.size()

def get_variable(root, path):
    if path[0] == '.':
        path = path[1:]
    attr_names = path.split('.')
    try:
        this_dir = root
        for attr_name in attr_names:
            this_dir = getattr(this_dir, attr_name)
    except AttributeError as e:
        raise AttributeError("Cannot find dir %s %s: message %s" % (attr_name, path, str(e)))
    return this_dir


class StructureBase(object):

    def values(self):
        print("not here")
        raise Exception("values needs defining")

    def keys(self):
        raise Exception("keys needs defining")

    def clear(self, item=None):
        raise Exception("clear needs defining")

    def get_item(self, key):
        raise Exception("get_items needs defining")

    def set_item(self, key, value):
        raise Exception("get_items needs defining")

    def items(self):
        return zip(self.keys(), self.values())

    def structure(self):
        if hasattr(self, 'select'):
            struct = self.select()
        else:
            struct = self.items()
        return struct

    def set_parent(self, parent):
        self._parent = weakref.ref(parent)
        self.update_selectors()

    def get_parent(self):
        try:
            return self._parent()
        except AttributeError:
            return None

    def root(self):
        return self.path()[0]

    def path(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.path() + [self]

    def update(self):
        self.unpack(self._buffer, self._offset)

    def update_selectors(self):
        if hasattr(self, 'select'):
            _ = list(self.select())
        for struct in self.values():
            struct.update_selectors()

    def pack(self):
        byte_data = bytes()
        for struct in self.values():
            byte_data += struct.pack()
        return byte_data

    def unpack(self, buffer, offset=0):
        self._offset = offset
        self._buffer = buffer
        index        = offset
        for key, struct in self.structure():
            index += struct.unpack(buffer, index)
        return index - offset

    def size(self):
        size_in_bytes = 0
        for struct in self.values():
            size_in_bytes += struct.size()
        return size_in_bytes

    def get_format(self):
        out = []
        for struct in self.values():
            out += struct.get_format()
        return out

    def set_values(self, value):
        index = 0
        for k, v in self.structure():
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

    def str_struct(self, depth=0):
        out = ''
        for key, val in self.items():
            if hasattr(val, 'str_struct'):
                out += '\t' * depth + str(key) + ':- \n'
                out += val.str_struct(depth + 1)
            else:
                out += '\t' * depth + str(key) + ': ' + str(val) + '\n'
        return out

    def __repr__(self):
        out = []
        for key, val in self.items():
            out.append("%s: %s" % (str(key), val.__class__.__name__))
        return ', '.join(out)

    def __str__(self):
        return self.str_struct()

    def __mul__(self, other):
        return StructureList([self() for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([self() for _ in range(int(other))])


class Structure(ClassDesc, StructureBase):
    STORE    = OrderedDict
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

    def clear(self, item=None):
        if item is None:
            self._store_.clear()
        else:
            del self._store_[item]

    def values(self):
        return self._store_.values()

    def keys(self):
        return self._store_.keys()

    def set_item(self, key, val):
        super(Structure, self).__setattr__(key, val)

    def add_field(self, name, type_val, length=None):
        if isinstance(type(type_val), type):
            type_val = type_val()

        if length is None:
            setattr(self, name, type_val)
        elif length is not None:
            setattr(self, name, type_val * length)
        return (name, type_val)

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


class StructureList(ListDesc, StructureBase):

    def values(self):
        return self

    def keys(self):
        return range(len(self))

    def clear(self, item=None):
        if item is None:
            del self[:]
        else:
            self.remove(item)

    def get_item(self, key):
        return list.__getitem__(self, key)

    def set_item(self, key, value):
        list.__setitem__(self, key, value)


class Selector(DynamicDescriptor, StructureBase):

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.internal_value = None

    def select(self, **kwargs):
        raise Exception("select method needs defining")

    def __dget__(self, instance, owner):
        return self.internal_value

    def __dset__(self, instance, value):
        raise AttributeError("Cannot set Selector")

    def set_values(self, values):
        self.update_selectors()
        return self.internal_value.set_values(values)

    def values(self):
        return self.internal_value.values()

    def keys(self):
        return self.internal_value.keys()

    def structure(self):
        return self.internal_value.structure()

    def update(self):
        if self.internal_value is None:
            raise Exception("Selector needs to be initialized call unpack() on it")
        return self.internal_value.update(self._buffer)

    def update_selectors(self):
        self.internal_value = self.select(**self.kwargs)

    def pack(self):
        if self.internal_value is None:
            raise Exception("Selector needs to be initialized call unpack() on it")
        return self.internal_value.pack()

    def unpack(self, buffer, offset=0):
        index = 0
        self._offset = offset
        self._buffer = buffer
        self.internal_value = self.select(**self.kwargs)
        index += self.internal_value.unpack(buffer, index + offset)
        return index

    def get_format(self):
        out = []
        for struct in self.internal_value.values():
            out += struct.get_format()
        return out




if __name__ == "__main__":
    class SelfStruct(Structure):

        def select(self):
            root = self.root()

            yield self.add_field('figit', UINT32)

            if self.figit > 100:
                yield self.add_field('type', UINT64)
            else:
                yield self.add_field('type', UINT16)

    class DynamicArray(Selector):
        def select(self, **kwargs):
            size     = get_variable(self.root(), kwargs['length'])
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
            self.options = SelfStruct()
            self.data = DynamicArray(length='length', type=UINT8)

    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    hd = EncapsulationHeader()#.build_with_values(0,5,2,3,4,5,6,7,8,9,10,11,12,13,14)

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
    hd.options.c = 0
    d = hd.pack()
    print(data)
    print(d.encode("hex"))
    print(hd)

    i=1




