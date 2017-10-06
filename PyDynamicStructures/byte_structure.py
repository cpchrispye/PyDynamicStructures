from PyDynamicStructures.meta import MetaDictClass, MetaList
from abc import ABCMeta, abstractmethod, abstractproperty
from PyDynamicStructures.utils import *
from collections import OrderedDict

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
    def _rebuild(self, key, value):
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

    # @abstractproperty
    # def _state_(self):
    #     pass

    def _set_hook_(self, key, value):
        if not isinstance(value, VirtualStructure):
            raise Exception("Only subclasses of VirtualStructure allowed to be set")
        value.set_parent(self)
        if hasattr(self._state_, 'set_method') and self._state_.set_method is not None:
            method, args, kwargs = self._state_.set_method
            getattr(value, method)(key, value, *args, **kwargs)

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        if hasattr(self, 'structure'):
            method, args, kwargs = self._state_.set_method
            kwargs['old_vals'] = self.structured_values
            self.set_process_attribute(method, *args, **kwargs)
            self.m.clear()
            result = self.structure()
            if result is not None:
                self._state_.internal_value = result
                #self.make_descriptor()
            self._state_.old_structure = None
        for key, val in self.m.items():
            self.process_attribute(key, val)
        self.set_process_attribute(None)

    def process_attribute(self, key, val):
        val.set_parent(self)
        if self._state_.set_method is not None:
            method, args, kwargs = self._state_.set_method
            getattr(val, method)(key, val, *args, **kwargs)

    def set_process_attribute(self, method, *args, **kwargs):
        if method is None:
            self._state_.set_method = None
        else:
            self._state_.set_method = (method, args, kwargs)

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
            self._state_.buffer = buffer
            self._state_.buffer_offset = buffer.offset
        else:
            self._state_.buffer.offset = self._state_.buffer_offset

        result = self.build('_unpack', self._state_.buffer)

    def rebuild(self):
        self.build('_rebuild')

    def set_values(self, values):
        self.build('_set_values', MasterValues(values, 0))

    def _pack(self):
        out = bytes()
        for item in self.m:
            out += item._pack()
        return out

    def _unpack(self, key, value, buffer_wrapper):
        value.unpack(buffer_wrapper)

    def _rebuild(self, key, value, old_vals=None):
        if old_vals is not None:
            value.set_values(old_vals.get(key))
        else:
            value.rebuild()

    def _set_values(self, key, value, value_wrapper):
        if isinstance(value_wrapper.values, list):
            value.set_values(value_wrapper)
        elif isinstance(value_wrapper.values, dict):
            value.set_values(value_wrapper.values[key])
        else:
            raise Exception('values must be a lis or a dict not %s' % value_wrapper.values.__class__.__name__)

    def set_parent(self, parent):
        self._state_.parent = parent

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

if __name__ =='__main__':
    class enip(StructureClass):
        pass
    a = StructureClass()
    a.fred = enip()
    m = a.m

    i=1
