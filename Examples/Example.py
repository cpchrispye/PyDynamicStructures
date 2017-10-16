from PyDynamicStructures.dynamic_structure import StructureClass, StructureList, BitStructure, BitStructureL
from PyDynamicStructures.base_types import UINT8, UINT16, UINT32, UINT64, EMPTY, BitElement
from PyDynamicStructures.pre_builts import Array

import timeit

class EncapsulationHeader(StructureClass):
    _size_ = 50

    def structure(self):
        self.command        = UINT16()
        self.length         = UINT8()
        self.session_handle = UINT32()
        self.status         = UINT32()
        self.sender_context = sub_header()
        self.options        = Flags()
        self.data           = Array('../length', UINT8)

class sub_header(StructureClass):
    def structure(self):
        self.mega = UINT16()

        if self.mega > 0:
            self.vv = UINT64()
        else:
            self.j = UINT16() * 3

class Flags(BitStructure):
    _low_first_ = False
    def structure(self):
        self.a1 = BitElement(2)
        self.a2 = BitElement(2)
        self.a3 = BitElement(2)
        self.a4 = BitElement(2)
        self.a5 = BitElement(2)
        self.a6 = BitElement(2)
        self.a7 = BitElement(2)
        self.a8 = BitElement(2)
        #self.a9 = BitElement(4)
        #self.set_size(5)

data = ''.join(['%02x' % i for i in range(255)])
header_data = data.decode("hex")

# yy = '041f'.decode("hex")
#
# myFlag = Flags()
# myFlag.unpack(yy)

enip = EncapsulationHeader(command=10,
                           length=30)





print(enip.size())
enip.command = 10
enip.rebuild()
enip.unpack(header_data)
datap = enip.pack()

print(datap.encode('hex'))
print(data)
m = enip.structured_values

i=1

