from PyDynamicStructures.descriptors import DynamicDescriptor, ClassDesc, ListDesc, GETTER, SETTER
from PyDynamicStructures.utils import MasterValues, MasterBuffer
from collections import Sequence, OrderedDict
import weakref
import types
import copy

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

    def __alt_init__(self):
        self.__method = None
        self.store.set_hook(self)

    @property
    def attributes(self):
        return self.store.dict()

    @property
    def store(self):
        raise Exception("store needs defining")
        return #type: AttributeStore

    @property
    def has_dynamic_structure(self):
        return hasattr(self, 'structure')

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        if self.has_dynamic_structure:
            self.__old_structure = self.get_struc_values()
            self.store.clear()
            result = self.structure()
            if result is not None:
                self._internal_value = result
                self.make_descriptor()
        for key, val in self.store.items():
            self.process_attribute(key, val)
        self.set_process_attribute(None)

    def set_parent(self, parent):
        self._parent = weakref.ref(parent)
        #parent.update()

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

    def pack(self):
        out = bytes()
        for struct in self.store.values():
            out += struct.pack()
        return out

    def unpack(self, buffer=None):
        if buffer is not None:
            if not isinstance(buffer, MasterBuffer):
                buffer = MasterBuffer(buffer, 0)
            self.__buffer = buffer
            self.__buffer_offset = self.__buffer.offset
        else:
            self.__buffer.offset = self.__buffer_offset

        result = self.build('_unpack', self.__buffer)


    def _unpack(self, key, val, master_buffer):
        val.unpack(master_buffer)

    def update(self):
        self.build('_update')

    def _update(self, key, val):
        if self.has_dynamic_structure:
            values = self.__old_structure.get(key)
            val.set_values(values)
        else:
            val.update()

    def set_values(self, values):
        if values is not None:
            if not isinstance(values, MasterValues):
                values = MasterValues(values, 0)
            self.__values = values
            self.__values_offset = self.__values.offset
        else:
            self.__values.offset = self.__values_offset

        result = self.build('_set_values', self.__values)

    def _set_values(self, key, val, master_values):
        if isinstance(master_values.values, list):
            val.set_values(master_values)
        else:
            val.set_values(master_values.values[key])

    def process_attribute(self, key, val):
        val.set_parent(self)
        if self.__method is not None:
            method, args, kwargs = self.__method
            getattr(self, method)(key, val, *args, **kwargs)

    def set_process_attribute(self, method, *args, **kwargs):
        if method is None:
            self.__method = None
        else:
            self.__method = (method, args, kwargs)

    def __repr__(self):
        out = []
        for key, val in self.store.items():
            out.append("%s: %s" % (str(key), val.__class__.__name__))
        return ', '.join(out)

    # def __str__(self):
    #     return self.str_struct()

    def __mul__(self, other):
        return StructureList([self() for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([self() for _ in range(int(other))])


class Structure(ClassDesc, StructureBase):
    _fields_ = []

    def __new__(cls, *args, **kwargs):
        new_instance = super(Structure, cls).__new__(cls)
        new_instance.__alt_init__()
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

    @property
    def store(self):
        return self._store_#type: AttributeStore

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

    @property
    def store(self):
        return self

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







