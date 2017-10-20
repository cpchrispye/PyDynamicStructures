from .descriptors import DescriptorDictClass, DescriptorList
from abc import ABCMeta, abstractmethod, abstractproperty
from .utils import *
from collections import OrderedDict, Mapping
from copy import copy
from weakref import ref

__all__ = ['DynamicClass', 'StructureClass', 'StructureList', 'DynamicList', 'StructureSelector', 'BitStructure', 'BitStructureL']

class VirtualStructure(object):
    __metaclass__ = ABCMeta
    #__slots__ = ()

    @abstractproperty
    def structured_values(self):
        pass

    @abstractmethod
    def slave_pack(self):
        pass

    @abstractmethod
    def slave_unpack(self, key, value, buffer_wrapper):
        pass

    @abstractmethod
    def slave_set_values(self, key, value, value_wrapper):
        pass

    @abstractmethod
    def set_parent(self, parent):
        pass

    @abstractmethod
    def size(self):
        pass


class BaseStructure(VirtualStructure):
    __metaclass__ = ABCMeta
    #__slots__ = ('st_args', 'st_kwargs', 'st_set_method', 'st_buffer_cache', 'st_parent', 'st_byte_size')

    def __init__(self, *args , **kwargs):
        st_size = kwargs.get('st_size')
        self.st_args = args
        self.st_kwargs = kwargs
        if hasattr(self, '_size_'):
            self.set_size(self._size_)
        elif st_size is not None:
            self.set_size(st_size)
            del kwargs['st_size']
        else:
            self.structure(*self.st_args, **self.st_kwargs)

    @classmethod
    def from_values(cls, *args, **kwargs):
        ins = cls()
        if args:
            ins.set_values(args)
        elif kwargs:
            ins.set_values(kwargs)
        return ins

    @classmethod
    def from_buffer(cls, buffer):
        ins = cls()
        ins.unpack(buffer)
        return ins


    @abstractproperty
    def m(self):
        pass

    @abstractmethod
    def structure(self):
        pass

    def _set_hook_(self, key, value):
        if isinstance(value, VirtualStructure):
            self.process_attribute(key, value)
            return True
        return False

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        self.m.clear()
        self.structure(*self.st_args, **self.st_kwargs)
        self.set_process_attribute(None)

    def process_attribute(self, key, val):
        val.set_parent(self)
        if hasattr(self, 'st_set_method') and self.st_set_method is not None:
            method, args, kwargs = self.st_set_method
            getattr(val, method)(key, *args, **kwargs)

    def set_process_attribute(self, method, *args, **kwargs):
        if method is None:
            self.st_set_method = None
        else:
            self.st_set_method = (method, args, kwargs)

    @property
    def structured_values(self):
        out = OrderedDict()
        for key, val in self.m.items():
            out[key] = val.structured_values
        return out

    def pack(self):
        return self.slave_pack()

    def unpack(self, buffer=None):
        if buffer is not None:
            mbuffer = MasterBuffer(buffer, 0)
            self.st_buffer_cache = copy(mbuffer)
        else:
            mbuffer = copy(self.st_buffer_cache)
        result = self.build('slave_unpack', mbuffer)

    def rebuild(self):
        self.build('slave_set_values', self.structured_values)

    def set_values(self, values):
        if isinstance(values, (list, tuple)):
            self.build('slave_set_values', MasterValues(values, 0))
        elif isinstance(values, (dict, OrderedDict)):
            self.build('slave_set_values', values)
        else:
            raise Exception('values must be a list or a dict not %s' % values.__class__.__name__)

    def slave_pack(self):
        out = bytes()
        for item in self.m.values():
            out += item.slave_pack()
        return out

    def slave_unpack(self, key, buffer_wrapper):
        self.build('slave_unpack', buffer_wrapper)

    def slave_set_values(self, key, values):
        val = get_values(key, values)
        if val is not None:
            self.build('slave_set_values', val)

    def set_parent(self, parent):
        self.st_parent = ref(parent)

    def get_parent(self):
        try:
            return self.st_parent()
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

    def st_format(self):
        format = []
        for val in self.m.values():
            format += val.st_format()
        return format

    def set_size(self, byte_size):
        self.st_byte_size = byte_size

    def size(self):
        s = self.fixed_size()
        if s is None:
            return self.struct_size()
        return s

    def struct_size(self):
        size = 0
        for val in self.m.values():
            size += val.size()
        return size

    def fixed_size(self):
        if hasattr(self, 'st_byte_size'):
            return self.st_byte_size
        return None

    def __repr__(self):
        out = []
        for key, val in self.m.items():
            out.append("%s: %s" % (str(key), val.__class__.__name__))
        return ', '.join(out)

    @property
    def hex(self):
        return self.slave_pack().encode('hex')

    # def __str__(self):
    #     return self.str_struct()

    def __mul__(self, other):
        return StructureList([type(self).from_values(**dict(self.structured_values)) for _ in range(int(other))])

    def __rmul__(self, other):
        return StructureList([type(self).from_values(**dict(self.structured_values)) for _ in range(int(other))])


class DynamicClass(DescriptorDictClass, BaseStructure):
    pass
    #__slots__ = ()


class StructureClass(DescriptorDictClass, BaseStructure):
    #__slots__ = ()

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        for key, val in self.m.items():
            self.process_attribute(key, val)
        self.set_process_attribute(None)



class StructureList(DescriptorList, BaseStructure):
    __slots__ = ()

    def __init__(self, seq=None, data_type=None, max_size=None):
        super(StructureList, self).__init__()
        if seq is not None:
            for i in seq:
                self.append(i)
            return

        if data_type is not None and max_size is not None:
            self.st_data_type = data_type
            self.st_max_size = max_size

    def structure(self):
        pass

    def build(self, method, *args, **kwargs):
        self.set_process_attribute(method, *args, **kwargs)
        for key, val in self.m.items():
            self.process_attribute(key, val)
        self.set_process_attribute(None)

    @property
    def structured_values(self):
        out = list()
        for val in self.m:
            out.append(val.structured_values)
        return out


class DynamicList(DescriptorList, BaseStructure):
    __slots__ = ()

    @classmethod
    def from_values(cls, *args, **kwargs):
        ins = cls()
        if args:
            ins.set_values(args)
        elif kwargs:
            ins.set_values(kwargs)
        return ins

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

    def slave_pack(self):
        return self.internal_value.slave_pack()

    def slave_unpack(self, key, buffer_wrapper):
        self.internal_value = self.structure(*self.args, **self.kwargs)
        return self.internal_value.slave_unpack(key, buffer_wrapper)

    def slave_set_values(self, key, value_wrapper):
        self.internal_value = self.structure(*self.args, **self.kwargs)
        #return self.internal_value._unpack(key, value_wrapper)

    def set_parent(self, parent):
        self.parent = parent
        self.internal_value = self.structure(*self.args, **self.kwargs)

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

    def struct_size(self):
        if self.internal_value is None:
            return 0
        return self.internal_value.struct_size()

    def fixed_size(self):
        return None

    def _getter_(self, instance):

        if hasattr(self.internal_value, '_getter_'):
            return self.internal_value._getter_(self)
        return self.internal_value


class BitStructure(DynamicClass):
    LENDIAN = False
    _low_first_ = True

    def slave_pack(self):
        val = 0
        bytes_size = self.size()
        items = self.m.values()
        if self._low_first_:
            items.reversed()
        for item in items:
            val <<= item.size()
            val |= item.slave_pack()
        out = bytes()
        for i in range(bytes_size):
            out += int_to_byte(255 & (val >> (8 * i)))
        if not self.LENDIAN:
            out = out[::-1]
        return out

    def unpack(self, buffer=None):
        if buffer is not None:
            mbuffer = MasterBuffer(buffer, 0)
            self.st_buffer_cache = copy(mbuffer)
        else:
            mbuffer = copy(self.st_buffer_cache)
        self.slave_unpack(None, mbuffer)

    def slave_unpack(self, key, buffer_wrapper):
        size = self.size()
        val = bytes_to_int(buffer_wrapper.buffer, size, buffer_wrapper.offset, self.LENDIAN)
        self.build('slave_unpack', MasterByte(val, 0, size*8, self._low_first_))
        buffer_wrapper.offset += size

    def set_size(self, byte_size):
        self.st_byte_size = byte_size

    def size(self):
        s = self.fixed_size()
        if s is None:
            return self.struct_size()
        return s

    def struct_size(self):
        size = 0
        for val in self.m.values():
            size += val.size()
        return bit_size_in_bytes(size)

    def fixed_size(self):
        if hasattr(self, 'st_byte_size'):
            return self.st_byte_size
        return None

class BitStructureL(BitStructure):
    LENDIAN = True

