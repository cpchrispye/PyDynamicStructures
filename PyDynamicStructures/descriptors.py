from collections import OrderedDict, MutableMapping, MutableSequence
from abc import ABCMeta, abstractmethod
GETTER = '_getter_'
SETTER = '_setter_'


class DescriptorItem(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def _getter_(self, instance):
        pass

    @abstractmethod
    def _setter_(self, instance, value):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if hasattr(subclass, GETTER):
            return True
        return NotImplemented

class DictStore(MutableMapping):

    def __init__(self, *args, **kwargs):
        self._store_ = OrderedDict(*args, **kwargs)

    def __getitem__(self, item):
        return self._store_.__getitem__(item)

    def __setitem__(self, key, value):
        self._store_.__setitem__(key, value)

    def __delitem__(self, key):
        self._store_.__delitem__(key)

    def __getattr__(self, item):
        if item == '_store_':
            return super(DictStore, self).__getattr__(item)
        return self._store_.__getitem__(item)

    def __setattr__(self, key, value):
        if key == '_store_':
            super(DictStore, self).__setattr__(key, value)
        else:
            self._store_.__setitem__(key, value)

    def __delattr__(self, item):
        self._store_.__delitem__(item)

    def __len__(self):
        return self._store_.__len__()

    def __iter__(self):
        return self._store_.__iter__()

    def getattr(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError()

    def get(self,item, default=None):
        if item in self:
            return self.getattr(item)
        return default

    def setattr(self, key, value):
        self.__setitem__(key, value)


class ListStore(MutableSequence):
    def __init__(self, *args, **kwargs):
        self._store_ = list(*args, **kwargs)

    def __getitem__(self, item):
        return self._store_.__getitem__(item)

    def __setitem__(self, key, value):
        self._store_.__setitem__(key, value)

    def __delitem__(self, key):
        self._store_.__delitem__(key)

    def __getattr__(self, item):
        if item == '_store_':
            return super(ListStore, self).__getattr__(item)
        return self._store_.__getitem__(item)

    def __setattr__(self, key, value):
        if key == '_store_':
            super(ListStore, self).__setattr__(key, value)
        else:
            self._store_.__setitem__(key, value)

    def __delattr__(self, item):
        self._store_.__delitem__(item)

    def __len__(self):
        return self._store_.__len__()

    def insert(self, index, value):
        self._store_.insert(index, value)

    def getattr(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError()

    def get(self,item, default=None):
        if item in self:
            return self.getattr(item)
        return default

    def setattr(self, key, value):
        self.__setitem__(key, value)

    def keys(self):
        return range(len(self))

    def values(self):
        return self

    def items(self):
        return zip(self.keys(), self.values())

class StateDict(object):

    def __init__(self):
        self.store = DictStore()
        self.set_visitor = None


class DescriptorClass(object):
    #__slots__ = ('_state_',)

    @property
    def m(self):
        return self._state_.store

    @property
    def s(self):
        return self._state_

    def __getattr__(self, item):
        if item == '_state_':
            super(DescriptorClass, self).__setattr__('_state_', StateDict())
            return self._state_
        try:
            found_item = self.m.getattr(item)
        except KeyError:
            raise AttributeError()
        if hasattr(found_item, GETTER):
            return getattr(found_item, GETTER)(self)
        return found_item

    def __setattr__(self, key, value):
        last_value = self.m.get(key)
        if (hasattr(last_value, GETTER)):
            getattr(last_value, SETTER)(self, value)
        else:
            if hasattr(self, '_set_hook_'):
                self._set_hook_(key, value)
            self.m.setattr(key, value)


class DescriptorDict(MutableMapping, object):
    #__slots__ = ('_state_',)
    
    @property
    def m(self):
        return self._state_.store

    @property
    def s(self):
        return self._state_

    def __getattr__(self, item):
        if item == '_state_':
            super(DescriptorDict, self).__setattr__('_state_', ListStore())
            return self._state_
        raise AttributeError()

    def __getitem__(self, item):
        try:
            item = self.m.getattr(item)
        except KeyError:
            raise AttributeError()
        if hasattr(item, GETTER):
            return getattr(item, GETTER)(self)
        return item

    def __setitem__(self, key, value):
        last_value = self.m.get(key)
        if (hasattr(last_value, GETTER)):
            getattr(last_value, SETTER)(self, value)
        else:
            if hasattr(self, '_set_hook_'):
                self._set_hook_(key, value)
            self.m.setattr(key, value)

    def __delitem__(self, key):
        self.m.__delitem__(key)
        
    def __len__(self):
        return self._state_._store_.__len__()

    def __iter__(self):
        self._state_._store_.__iter__()


class DescriptorDictClass(DescriptorClass, DescriptorDict):
    #__slots__ = ('_state_',)
    pass


class StateList(object):
    def __init__(self):
        self.store = ListStore()
        self.set_visitor = None


class DescriptorList(MutableSequence, object):
    # __slots__ = ('_state_',)

    @property
    def m(self):
        return self._state_.store

    @property
    def s(self):
        return self._state_

    def __getattr__(self, item):
        if item == '_state_':
            super(DescriptorList, self).__setattr__('_state_', StateList())
            return self._state_
        raise AttributeError()

    def __getitem__(self, item):
        try:
            item = self.m.getattr(item)
        except KeyError:
            raise KeyError()
        if hasattr(item, GETTER):
            return getattr(item, GETTER)(self)
        return item

    def __setitem__(self, key, value):
        last_value = self.m.get(key)
        if (hasattr(last_value, GETTER)):
            getattr(last_value, SETTER)(self, value)
        else:
            if hasattr(self, '_set_hook_'):
                self._set_hook_(key, value)
            self.m.setattr(key, value)

    def __delitem__(self, key):
        self.m.__delitem__(key)

    def __len__(self):
        return self._state_.store.__len__()

    def insert(self, index, value):
        self._state_.store.insert(index, value)

    def items(self):
        return zip(range(len(self)), self)