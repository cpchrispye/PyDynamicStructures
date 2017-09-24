SETTER = '__dset__'
GETTER = '__dget__'

class DynamicDescriptor(object):

    def __dget__(self, instance, owner):
        pass

    def __dset__(self, instance, value):
        pass

class ClassDesc(object):

    def __getattr__(self, item):
        if item == '_store_':
            super(ClassDesc, self).__setattr__('_store_', self.STORE())
            return self._store_
        try:
            item = self._store_[item]
        except KeyError:
            raise AttributeError()
        if hasattr(item, GETTER):
            return getattr(item, GETTER)(None, None)
        return item

    def __setattr__(self, key, value):
        if isinstance(value, (ClassDesc, DynamicDescriptor)):
            if hasattr(value, 'set_parent'):
                value.set_parent(self)
            self._store_[key] = value
        elif(hasattr(self._store_.get(key), GETTER)):
            getattr(self._store_[key], SETTER)(self, value)
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
