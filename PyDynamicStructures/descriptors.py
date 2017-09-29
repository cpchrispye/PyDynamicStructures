from collections import OrderedDict, Iterable

SETTER = '__dset__'
GETTER = '__dget__'

class DynamicDescriptor(object):

    def __dget__(self, instance, owner):
        pass

    def __dset__(self, instance, value):
        pass

class ClassDesc(object):
    STORE_TYPE = AttributeStore

    def __getattr__(self, item):
        if item == '_store_':
            super(ClassDesc, self).__setattr__('_store_', self.STORE())
            return self._store_
        try:
            item = self._store_.get_item(item)
        except KeyError:
            raise AttributeError()
        if hasattr(item, GETTER):
            return getattr(item, GETTER)(None, None)
        return item

    def __setattr__(self, key, value):
        if isinstance(value, (ClassDesc, DynamicDescriptor)):
            if hasattr(value, 'set_parent'):
                value.set_parent(self)
            self._store_.set_item(key, value)
        elif(hasattr(self._store_.get(key), GETTER)):
            getattr(self._store_key.get_item(key), SETTER)(self, value)
        else:
            super(ClassDesc, self).__setattr__(key, value)


class ListDesc(list):
    def __getitem__(self, item):

        item = super(ListDesc, self).__getitem__(item)
        if hasattr(item, GETTER):
            return getattr(item, GETTER)(None, None)
        return item

    def __setitem__(self, key, value):
        if isinstance(value, (ClassDesc, DynamicDescriptor)):
            value.set_parent(self)
            super(ListDesc, self).__setitem__(key, value)
        elif (hasattr(self[key], GETTER)):
            getattr(self[key], SETTER)(None, None)
        else:
            raise TypeError()


def smooth_iterable(store, iter):
    index = 0
    for i, _ in enumerate(iter):
        new_attr = store.items()[index:]
        for attr in new_attr:
            yield attr
        index += len(new_attr)


class AttributeStore(object):

    def __init__(self):
        self._store_ = OrderedDict()

    def set_item(self, key, val):
        self._store_[key] = val

    def get_item(self, key):
        return self._store_[key]

    def get(self, key, default=None):
        return self._store_.get(key, default)

    def keys(self):
        return self._store_.keys()

    def values(self):
        return self._store_.values()

    def items(self):
        return self.items()

    def build_attributes(self, method, instance):
        attributes = method(instance)
        if attributes is None:
            return self.items()
        elif issubclass(attributes, Iterable):
            return smooth_iterable(self, attributes)
        elif issubclass(attributes, (ClassDesc, ListDesc, DynamicDescriptor)):
            return attributes
        else:
            raise Exception("%s method on %s class returns incorrect value" %
                            (method.__class__.__name__, instance.__class__.__name__))






