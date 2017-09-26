from PyDynamicStructures.dynamic_structure import Structure, StructureList, Selector, get_variable
from PyDynamicStructures.base_types import *

if __name__ == "__main__":
    class SelfStruct(Structure):

        def build(self):
            root = self.root()

            yield self.add_field('figit', UINT32)

            if self.figit > 100:
                yield self.add_field('type', UINT64)
            else:
                yield self.add_field('type', UINT16)

    class DynamicArray(Selector):
        def select(self, **kwargs):
            size     = get_variable(self.root(), kwargs['length'])
            str_type = kwargs['type']()
            return str_type * size

    class sub(Structure):
        def __init__(self):
            self.a = UINT8()
            self.b = UINT32()


    class sub_alt(Structure):
        _fields_ = [
            ("c", UINT8),
            ("f", UINT16),
        ]


    class EncapsulationHeader(Structure):
        def __init__(self):
            self.command = UINT16()
            self.length = UINT8()
            self.session_handle = UINT32()
            self.status = UINT32()
            self.sender_context = UINT64()
            self.options = SelfStruct()
            self.data = DynamicArray(length='length', type=UINT8)

    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    hd = EncapsulationHeader()#.build_with_values(0,5,2,3,4,5,6,7,8,9,10,11,12,13,14)

    hd.unpack(header_data)
    v = hd.command
    d = hd.pack()
    print(d.encode('hex'))
    print(data)
    alt_struct = sub_alt(3, 5)
    hd.options = alt_struct
    hd.update()
    hd.length = 10
    hd.update_selectors()
    print(hd.get_format())
    hd.options.c = 0
    d = hd.pack()
    print(data)
    print(d.encode("hex"))
    print(hd)
    print(hd.__repr__())

    i=1
