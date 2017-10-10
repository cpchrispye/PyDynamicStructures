from PyDynamicStructures.dynamic_structure import StructureClass, StructureList, Array, BitStructure, BitStructureL
from PyDynamicStructures.base_types import UINT8, UINT16, UINT32, UINT64, EMPTY, BitElement


class EncapsulationHeader(StructureClass):
    def __init__(self):
        self.command        = UINT16()
        self.length         = UINT8()
        self.session_handle = UINT32()
        self.status         = UINT32()
        self.sender_context = UINT64()
        self.options        = Flags()
        #self.data           = Array('../length', UINT8)

class sub_header(StructureClass):
    def structure(self):
        self.mega = UINT16()

        if self.mega > 0:
            self.vv = UINT64()
        else:
            self.j = UINT16() * 3

class Flags(BitStructureL):

    def __init__(self):
        self.a1 = BitElement(2)
        self.a2 = BitElement(2)
        self.a3 = BitElement(2)
        self.a4 = BitElement(2)
        self.a5 = BitElement(2)
        self.a6 = BitElement(2)
        self.a7 = BitElement(2)
        self.a8 = BitElement(2)


data = ''.join(['%02x' % i for i in range(255)])
header_data = data.decode("hex")

yy = '041f'.decode("hex")

myFlag = Flags()
myFlag.unpack(yy)

enip = EncapsulationHeader()
enip.command = 10
enip.rebuild()
enip.unpack(header_data)
datap = enip.pack()

print(datap.encode('hex'))
print(data)
m = enip.structured_values

i=1

