from PyDynamicStructures.descriptors import DynamicDescriptor, ClassDesc, ListDesc
from collections import Sequence, OrderedDict, Iterable
import weakref

__all__ = ['Structure', 'StructureList', 'Selector', 'StructureBit', 'sizeof', 'get_variable']

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

    def __init__(self, *args, **kwargs):
        self.args   = args
        self.kwargs = kwargs

    def values(self):
        print("not here")
        raise Exception("values needs defining")

    def keys(self):
        raise Exception("keys needs defining")

    def clear(self, item=None):
        raise Exception("clear needs defining")

    def items(self):
        return zip(self.keys(), self.values())

    def set_parent(self, parent):
        self._parent = weakref.ref(parent)
        self.update()

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
        if hasattr(self, 'build'):
            old_store = self._store_
            for key, val in self.build_manager():
                old_val = old_store.get(key)
                if type(old_val) == type(val):
                    val.set_values(old_val.base_values())
        else:
            for val in self.values():
                val.update()

    def build_manager(self):
        if hasattr(self, 'build'):
            self._store_ = self.STORE()
            stop_points = self.build()
            if isinstance(stop_points, Iterable):
                index = 0
                for _ in stop_points:
                    for item in self.items()[index:]:
                        yield item
                        index += 1
                for item in self.items()[index:]:
                    yield item
                    index += 1
                raise StopIteration

        for item in self.items():
            yield item

    def pack(self):
        byte_data = bytes()
        for struct in self.values():
            byte_data += struct.pack()
        return byte_data

    def unpack(self, buffer=None, offset=0):
        if buffer is not None:
            self._offset = offset
            self._buffer = buffer
        if self._buffer is None:
            raise Exception('unpack must be call with buffer at least once')
        index = self._offset
        for key, struct in self.build_manager():
            index += struct.unpack(self._buffer, index)
        return index - self._offset

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
        for k, v in self.build_manager():
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

    def base_values(self):
        values = []
        for v in self.values():
            values += v.base_values()
        return values

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
    _fields_ = []

    def __new__(cls, *args, **kwargs):
        new_instance = super(Structure, cls).__new__(cls)
        new_instance.add_fields(cls._fields_)
        return new_instance

    @classmethod
    def from_values(cls, *args, **kwargs):
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

    def items(self):
        return self._store_.items()

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
        self.internal_value = self.select(**self.kwargs)

    def pack(self):
        if self.internal_value is None:
            raise Exception("Selector needs to be initialized call unpack() on it")
        return self.internal_value.pack()

    def unpack(self, buffer=None, offset=0):
        if buffer is not None:
            self._offset = offset
            self._buffer = buffer
        if self._buffer is None:
            raise Exception('unpack must be call with buffer at least once')
        index = self._offset
        self.internal_value = self.select(**self.kwargs)
        index + self.internal_value.unpack(self._buffer, index)
        return index

    def base_values(self):
        return self.internal_value.base_values()

    def get_format(self):
        out = []
        for struct in self.internal_value.values():
            out += struct.get_format()
        return out


class StructureBit(ClassDesc, StructureBase):
    STORE = OrderedDict

    def clear(self, item=None):
        if item is None:
            self._store_.clear()
        else:
            del self._store_[item]

    def values(self):
        return self._store_.values()

    def keys(self):
        return self._store_.keys()

    def items(self):
        return self._store_.items()







