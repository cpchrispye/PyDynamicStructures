from .descriptors import DescriptorDictClass, DescriptorList
from abc import ABCMeta, abstractmethod, abstractproperty
from .utils import *
from collections import OrderedDict, Mapping
from copy import copy

__all__ = ['DynamicClass', 'StructureClass', 'StructureList', 'StructureSelector', 'BitStructure', 'BitStructureL']

class VirtualStructure(object):
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractproperty
    def structured_values(self):
        pass

    @abstractmethod
    def _pack(self):
        pass

    @abstractmethod
    def _unpack(self, key, value, buffer_wrapper):
        pass

    @abstractmethod
    def _set_values(self, key, value, value_wrapper):
        pass

    @abstractmethod
    def set_parent(self, parent):
        pass

    @abstractmethod
    def size(self):
        pass


class BaseStructure(VirtualStructure):
    __metaclass__ = ABCMeta
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        self.structure()
        if args:
            self.set_values(args)
        elif kwargs:
            self.set_values(kwargs)
        if hasattr(self, '_size_'):
            self.set_size(self._size_)

    @abstractproperty
    def m(self):
        pass

    @abstractproperty
    def s(self):
        pass

    @abstractmethod
    def structure(self):
        pass

    def _set_hook_(self, key, value):
        if not isinstance(value, VirtualStructure):
            raise Exception("Only subclasses of VirtualStructure allowed to be set")
        self.process_attribute(key, value)

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        self.m.clear()
        self.structure()
        self.set_process_attribute(None)

    def process_attribute(self, key, val):
        val.set_parent(self)
        if hasattr(self.s, 'set_method') and self.s.set_method is not None:
            method, args, kwargs = self.s.set_method
            getattr(val, method)(key, *args, **kwargs)

    def set_process_attribute(self, method, *args, **kwargs):
        if method is None:
            self.s.set_method = None
        else:
            self.s.set_method = (method, args, kwargs)

    @property
    def structured_values(self):
        out = OrderedDict()
        for key, val in self.m.items():
            out[key] = val.structured_values
        return out

    def pack(self):
        return self._pack()

    def unpack(self, buffer=None):
        if buffer is not None:
            mbuffer = MasterBuffer(buffer, 0)
            self.s.buffer_cache = copy(mbuffer)
        else:
            mbuffer = copy(self.s.buffer_cache)
        result = self.build('_unpack', mbuffer)

    def rebuild(self):
        self.build('_set_values', self.structured_values)

    def set_values(self, values):
        if isinstance(values, (list, tuple)):
            self.build('_set_values', MasterValues(values, 0))
        elif isinstance(values, (dict, OrderedDict)):
            self.build('_set_values', values)
        else:
            raise Exception('values must be a list or a dict not %s' % values.__class__.__name__)

    def _pack(self):
        out = bytes()
        for item in self.m.values():
            out += item._pack()
        return out

    def _unpack(self, key, buffer_wrapper):
        self.build('_unpack', buffer_wrapper)

    def _set_values(self, key, value_wrapper):
        if isinstance(value_wrapper, MasterValues):
            self.build('_set_values', value_wrapper)
        elif isinstance(value_wrapper, (dict, OrderedDict)):
            self.build('_set_values', value_wrapper.get(key, {}))
        else:
            raise Exception('values must be a list or a dict not %s' % value_wrapper.values.__class__.__name__)

    def set_parent(self, parent):
        self.s.parent = parent

    def get_parent(self):
        try:
            return self.s.parent
        except AttributeError:
            return None

    def root(self):
        return self.get_parents()[0]

    def get_parents(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.path() + [self]

    def get_variable(self, path):
        return get_variable(self, path)

    def set_size(self, byte_size):
        self.s.byte_size = byte_size

    def size(self):
        if hasattr(self.s, 'byte_size'):
            return self.s.byte_size
        size = 0
        for val in self.m.values():
            size += val.size()
        return size

    def __repr__(self):
        out = []
        for key, val in self.m.items():
            out.append("%s: %s" % (str(key), val.__class__.__name__))
        return ', '.join(out)

    @property
    def hex(self):
        return self._pack().encode('hex')

    # def __str__(self):
    #     return self.str_struct()

    def __mul__(self, other):
        return StructureList([type(self).from_values(self.structured_values) for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([type(self).from_values(self.structured_values) for _ in range(int(other))])


class DynamicClass(DescriptorDictClass, BaseStructure):
    __slots__ = ()

    @classmethod
    def from_values(cls, *args, **kwargs):
        ins = cls()
        if args:
            ins.set_values(args)
        elif kwargs:
            ins.set_values(kwargs)
        return ins

class StructureClass(DescriptorDictClass, BaseStructure):
    __slots__ = ()

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        for key, val in self.m.items():
            self.process_attribute(key, val)
        self.set_process_attribute(None)

    @classmethod
    def from_values(cls, *args, **kwargs):
        ins = cls()
        if args:
            ins.set_values(args)
        elif kwargs:
            ins.set_values(kwargs)
        return ins

    @classmethod
    def from_list(cls, fields, size=None):
        cls()


class StructureList(DescriptorList, BaseStructure):
    __slots__ = ()

    def structure(self):
        pass


    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        for key, val in self.m.items():
            self.process_attribute(key, val)
        self.set_process_attribute(None)

    @classmethod
    def from_values(cls, *args, **kwargs):
        ins = cls()
        if args:
            ins.set_values(args)
        elif kwargs:
            ins.set_values(kwargs)
        return ins

    def __init__(self, seq=None):
        if seq is not None:
            for i in seq:
                self.append(i)

    @property
    def structured_values(self):
        out = list()
        for val in self.m:
            out.append(val.structured_values)
        return out

class StructureSelector(VirtualStructure):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.internal_value = None

    @abstractmethod
    def structure(self):
        pass

    @property
    def structured_values(self):
        return self.internal_value.structured_values

    def _pack(self):
        return self.internal_value._pack()

    def _unpack(self, key, buffer_wrapper):
        self.internal_value = self.structure()
        return self.internal_value._unpack(key, buffer_wrapper)

    def _set_values(self, key, value_wrapper):
        self.internal_value = self.structure()
        #return self.internal_value._unpack(key, value_wrapper)

    def set_parent(self, parent):
        self.parent = parent
        self.internal_value = self.structure()

    def get_parent(self):
        try:
            return self.parent
        except AttributeError:
            return None

    def root(self):
        return self.get_parents()[0]

    def get_parents(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.get_parents() + [self]

    def get_variable(self, path):
        return get_variable(self, path)

    def size(self):
        if self.internal_value is None:
            return 0
        return self.internal_value.size()

    def _getter_(self, instance):
        return self.internal_value


class BitStructure(StructureClass):
    LENDIAN = False

    def _pack(self):
        val = 0
        bytes_size = self.size()
        for item in self.m.values()[::-1]:
            val <<= item.size()
            val |= item._pack()
        out = bytes()
        for i in range(bytes_size):
            out += int_to_byte(255 & (val >> (8 * i)))
        if not self.LENDIAN:
            out = out[::-1]
        return out

    def unpack(self, buffer=None):
        if buffer is not None:
            mbuffer = MasterBuffer(buffer, 0)
            self.s.buffer_cache = copy(mbuffer)
        else:
            mbuffer = copy(self.s.buffer_cache)
        self._unpack(None, mbuffer)

    def _unpack(self, key, buffer_wrapper):

        val = bytes_to_int(buffer_wrapper.buffer, self.size(), buffer_wrapper.offset, self.LENDIAN)
        self.build('_unpack', MasterByte(val, 0))
        buffer_wrapper.offset += self.size()

    def set_size(self, byte_size):
        self.s.byte_size = byte_size

    def size(self):
        if hasattr(self.s, 'byte_size'):
            return self.s.byte_size
        size = 0
        for val in self.m.values():
            size += val.size()
        return bit_size_in_bytes(size)


class BitStructureL(BitStructure):
    LENDIAN = True


if __name__ =='__main__':
    class enip(StructureClass):
        pass
    a = StructureClass()
    a.fred = enip()
    m = a.m

    i=1
