from PyDynamicStructures.meta import MetaDictClass, MetaList

from abc import ABCMeta, abstractmethod, abstractproperty
from PyDynamicStructures.utils import *
from collections import OrderedDict, Mapping

class VirtualStructure(object):
    __metaclass__ = ABCMeta

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

    @abstractproperty
    def m(self):
        pass

    @abstractproperty
    def s(self):
        pass

    def _set_hook_(self, key, value):
        if not isinstance(value, VirtualStructure):
            raise Exception("Only subclasses of VirtualStructure allowed to be set")
        value.set_parent(self)
        if hasattr(self.s, 'set_method') and self.s.set_method is not None:
            method, args, kwargs = self.s.set_method
            getattr(value, method)(key, *args, **kwargs)

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        if hasattr(self, 'structure'):
            self.m.clear()
            self.structure()
        else:
            for key, val in self.m.items():
                self.process_attribute(key, val)
        self.set_process_attribute(None)

    def process_attribute(self, key, val):
        val.set_parent(self)
        if self.s.set_method is not None:
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
            if not isinstance(buffer, MasterBuffer):
                buffer = MasterBuffer(buffer, 0)
            self.s.buffer = buffer
            self.s.buffer_offset = buffer.offset
        else:
            self.s.buffer.offset = self.s.buffer_offset

        result = self.build('_unpack', self.s.buffer)

    def rebuild(self):
        self.build('_set_values', self.structured_values)

    def set_values(self, values):
        if isinstance(values, list):
            self.build('_set_values', MasterValues(values, 0))
        elif isinstance(values, (dict, OrderedDict)):
            self.build('_set_values', values)
        else:
            raise Exception('values must be a lis or a dict not %s' % values.__class__.__name__)

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
        return self.path()[0]

    def path(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.path() + [self]

    def size(self):
        out = 0
        for val in self.m:
            out += val.size()
        return out

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


class StructureClass(MetaDictClass, BaseStructure):

    @classmethod
    def from_values(cls, *args, **kwargs):
        ins = cls()
        if args:
            ins.set_values(args)
        elif kwargs:
            ins.set_values(kwargs)
        return ins


class StructureList(MetaList, BaseStructure):

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

    def structured_values(self):
        return self.internal_value.structured_values

    def _pack(self):
        return self.internal_value._unpack()

    def _unpack(self, key, value, buffer_wrapper):
        self.internal_value = self.structure()
        return self.internal_value._unpack(key, value, buffer_wrapper)

    def _set_values(self, key, value, value_wrapper):
        self.internal_value = self.structure()
        return self.internal_value._unpack(key, value, value_wrapper)

    def set_parent(self, parent):
        self.parent = parent
        self.internal_value = self.structure()

    def get_parent(self):
        try:
            return self.parent
        except AttributeError:
            return None

    def root(self):
        return self.path()[0]

    def path(self):
        parent = self.get_parent()
        if parent is None:
            return [self]
        return parent.path() + [self]

    def size(self):
        if self.internal_value is None:
            return 0
        return self.internal_value.size()

    def _getter(self, instance):
        return self.internal_value


class Array(StructureSelector):

    def __init__(self, var_path, type):
        self.var_path = var_path
        self.type = type

    def structure(self):



if __name__ =='__main__':
    class enip(StructureClass):
        pass
    a = StructureClass()
    a.fred = enip()
    m = a.m

    i=1
