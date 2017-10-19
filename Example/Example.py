from PyDynamicStructures import dynamic_structure as ds
from PyDynamicStructures import descriptors as de
from PyDynamicStructures import base_types as bt

class TestStruct(ds.StructureClass):
    def structure(self):
        self.test1 = bt.UINT16()
        self.test2 = bt.UINT8()


f = de.DictStore()
f.g = 0
f.h=3



base = de.DescriptorDictClass()


base.test = bt.UINT16()
test = TestStruct()

stop = True