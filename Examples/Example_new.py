from PyDynamicStructures.byte_structure import StructureClass, StructureList
from PyDynamicStructures.byte_types import UINT8, UINT16, UINT32, UINT64, EMPTY


class EncapsulationHeader(StructureClass):
    def __init__(self):
        self.command        = UINT16()
        self.length         = UINT8()
        self.session_handle = UINT32()
        self.status         = UINT32()
        self.sender_context = UINT64()
        self.options        = sub_header()
        self.data           = UINT8() * 6

class sub_header(StructureClass):
    def structure(self):
        self.mega = UINT16()

        if self.mega > 0:
            self.vv = UINT64()
        else:
            self.j = UINT16() * 3

enip = EncapsulationHeader()
enip.command = 10
enip.rebuild()
m = enip.structured_values

i=1

