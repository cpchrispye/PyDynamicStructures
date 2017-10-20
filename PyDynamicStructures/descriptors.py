from collections import OrderedDict, MutableMapping, MutableSequence
from abc import ABCMeta, abstractmethod
GETTER  = '_getter_'
SETTER  = '_setter_'
REPLACE = '_replace_'
DESCRIPTOR_FRAME_WORK = '_descriptor_fw_'


class Descriptor(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def _getter_(self, name):
        pass

    @abstractmethod
    def _setter_(self, name, val):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if hasattr(subclass, GETTER):
            return True
        return NotImplemented

    def __repr__(self):
        return str(self._getter_(None))


class DictStore(OrderedDict):

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, '_DictStore__setup_complete', False)
        super(DictStore, self).__init__(*args, **kwargs)
        self.__setup_complete = True

    def __getattr__(self, item):
        if self.__setup_complete == True:
            return self.__getitem__(item)
        return object.__getattr__(self, item)

    def __setattr__(self, key, item):
        if self.__setup_complete == False:
            object.__setattr__(self, key, item)
        else:
            self.__setitem__(key, item)

    def getitem(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError()

    def setitem(self, key, value):
        self.__setitem__(key, value)


class ListStore(list):

    def getitem(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError()

    def get(self,item, default=None):
        if item in self:
            return self.getattr(item)
        return default

    def setitem(self, key, value):
        self.__setitem__(key, value)

    def keys(self):
        return range(len(self))

    def values(self):
        return self

    def items(self):
        return zip(self.keys(), self.values())

    def clear(self):
        del self[:]


class DescriptorBase(object):
    __slots__ = ('_store_')
    _state_type_ = None

    @property
    def m(self):
        return self._store_

    def _set_hook_(self, key, value):
        try:
            return super(DescriptorBase, self)._set_hook_(key, value)
        except AttributeError:
            pass
        return True

    def _des_getattr_(self, key):
        if key == '_store_':
            store = self._state_type_()
            object.__setattr__(self, '_store_', store)
            return store
        try:
            found_item = self.m.getitem(key)
        except Exception:
            raise AttributeError()
        if hasattr(found_item, GETTER):
            return getattr(found_item, GETTER)(self)
        return found_item

    def _des_setattr_(self, key, value):
        if key not in self._store_:
            if self._set_hook_(key, value):
                self._store_.setitem(key, value)
            else:
                super(DescriptorBase, self).__setattr__(key, value)
        else:
            if self._set_hook_(key, value):
                self._store_.setitem(key, value)
            else:
                current_val = self._store_.getitem(key)
                if hasattr(current_val, SETTER) and not hasattr(value, GETTER):
                    getattr(current_val, SETTER)(key, value)
                    return
                self._store_[key] = value


class DescriptorClass(DescriptorBase):
    #__slots__ = ('_state_')
    _state_type_ = DictStore

    def __getattr__(self, item):
        return self._des_getattr_(item)

    def __setattr__(self, key, value):
        self._des_setattr_(key, value)


class DescriptorDict(MutableMapping, DescriptorBase):
    #__slots__ = ('_state_')
    _state_type_ = DictStore

    def __getitem__(self, item):
        return self._des_getattr_(item)

    def __setitem__(self, key, value):
        self._des_setattr_(key, value)

    def __delitem__(self, key):
        self.m.__delitem__(key)
        
    def __len__(self):
        return self.m.__len__()

    def __iter__(self):
        self.m.__iter__()


class DescriptorDictClass(DescriptorClass, DescriptorDict):
    #__slots__ = ()
    pass


class DescriptorList(MutableSequence, DescriptorBase):
    #__slots__ = ('_state_')
    _state_type_ = ListStore

    def __init__(self, *args, **kwargs):
        self._store_ = self._state_type_()
        super(DescriptorList, self).__init__(*args, **kwargs)

    def __getitem__(self, item):
        return self._des_getattr_(item)

    def __setitem__(self, key, value):
        self._des_setattr_(key, value)

    def __delitem__(self, key):
        self.m.__delitem__(key)

    def __len__(self):
        return self.m.__len__()

    def insert(self, key, value):
        if hasattr(self, '_set_hook_'):
            self._set_hook_(key, value)
        self.m.insert(key, value)

    def items(self):
        return zip(range(len(self)), self)