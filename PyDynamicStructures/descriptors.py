from collections import OrderedDict, Iterable
import weakref
import types
import inspect

SETTER = '__dset__'
GETTER = '__dget__'

class DynamicDescriptor(object):

    def __dget__(self, instance, owner):
        pass

    def __dset__(self, instance, value):
        pass

class AttributeStore(object):

    def __init__(self):
        self._store_ = OrderedDict()
        self.clear_set_hook()

    def set_item(self, key, val):
        if self.__visitor is not None:
            self.__visitor.process_attribute(key, val)
        self._store_[key] = val

    def get_item(self, key):
        return self._store_[key]

    def __getitem__(self, item):
        return self._store_[item]

    def __setitem__(self, key, value):
        self.set_item(self, key, value)

    def __len__(self):
        return len(self._store_)

    def get(self, key, default=None):
        return self._store_.get(key, default)

    def keys(self):
        return self._store_.keys()

    def values(self):
        return self._store_.values()

    def items(self):
        return self._store_.items()

    def dict(self):
        return dict(self._store_)

    def clear(self):
        self._store_.clear()

    def set_hook(self, visitor):
        self.__visitor = visitor

    def clear_set_hook(self):
        self.__visitor = None



class ClassDesc(object):
    STORE_TYPE = AttributeStore

    def __getattr__(self, item):
        if item == '_store_':
            super(ClassDesc, self).__setattr__('_store_', self.STORE_TYPE())
            return self._store_
        try:
            item = self._store_.get_item(item)
        except KeyError:
            raise AttributeError()
        if hasattr(item, GETTER):
            return getattr(item, GETTER)(self, type(self))
        return item

    def __setattr__(self, key, value):
        if isinstance(value, (ClassDesc, ListDesc, DynamicDescriptor)):
            self._store_.set_item(key, value)
        elif(hasattr(self._store_.get(key), GETTER)):
            getattr(self._store_.get_item(key), SETTER)(self, value)
        else:
            super(ClassDesc, self).__setattr__(key, value)

    def get_struc_values(self):
        out = OrderedDict()
        for key in self._store_.keys():
            val = self.__getattr__(key)
            if hasattr(val, 'get_struc_values'):
                val = val.get_struc_values()
            out[key] = val
        return out

    def make_descriptor(self):
        setattr(self, GETTER, self.internal_getter)
        setattr(self, SETTER, self.internal_setter)

    def remove_descriptor(self):
        del self.__dict__[GETTER]
        del self.__dict__[SETTER]
        del self._store_['__internal_value']

    def internal_getter(self, instance, owner):
        return self._internal_value

    def internal_setter(self, instance, value):
        self._internal_value = value



class ListDesc(list):
    STORE_TYPE = None

    def __getitem__(self, item):
        try:
            value = super(ListDesc, self).__getitem__(item)
        except KeyError:
            raise KeyError()
        if hasattr(value, GETTER):
            return getattr(value, GETTER)(None, None)
        return value

    def __setitem__(self, key, value):
        if isinstance(value, (ClassDesc, ListDesc, DynamicDescriptor)):
            if hasattr(self, '__visitor'):
                self.__visitor(key, value)
            super(ListDesc, self).__setitem__(key, value)
        elif(hasattr(self.get(key), GETTER)):
            getattr(self.get(key), SETTER)(self, value)
        else:
            super(ListDesc, self).__setitem__(key, value)

    def get(self, key, default=None):
        try:
            return self[key]
        except:
            return default

    def dict(self):
        return self

    def keys(self):
        return range(len(self))

    def values(self):
        return self

    def items(self):
        return zip(self.keys(), self)

    def clear(self):
        del self[:]

    def set_hook(self, visitor):
        self.__visitor = visitor

    def clear_set_hook(self):
        self.__visitor = None

    def get_struc_values(self):
        out = OrderedDict()
        for key in self.keys():
            val = self.__getitem__(key)
            if hasattr(val, 'get_struc_values'):
                val = val.get_struc_values()
            out[key] = val
        return out


def smooth_iterable(store, iter):
    index = 0
    for i, _ in enumerate(iter):
        new_attr = store.items()[index:]
        for attr in new_attr:
            yield attr
        index += len(new_attr)









