#from PyDynamicStructures.dynamic_structure import Structure, StructureList, Selector, get_variable
from PyDynamicStructures import *
from PyDynamicStructures.utils import *
import math
if __name__ == "__main__":
    class SelfStruct(Structure):

        def structure(self):
            root = self.root()
            self.command = UINT32()

            if self.command > 100:
                self.type = UINT64()

            else:
                self.type = UINT16()



    class DynamicArray(Structure):
        def structure(self):
            size     = get_variable(self.root(), self.kwargs['length'])
            str_type = self.kwargs['type']()
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

    # class MyBit(StructureBit):
    #
    #     def __init__(self, size=None):
    #         self.__size = size
    #         self.f1 = BitField(3)
    #         self.f2 = BitField(3)
    #         self.f3 = BitField(1)
    #         self.f4 = BitField(5)
    #
    #     def pack(self):
    #         val = 0
    #         size = self.size()
    #         bytes_size =  math.ceil(size /8.0)
    #         for item in self.values():
    #             val |= item.pack()
    #         out = []
    #         for i in xrange(bytes_size):
    #             out.append(255 & (val >> (8 ** i)))
    #         return bytes(out)
    #
    #     def unpack(self, buffer=None, offset=0):
    #         index = offset
    #         bits = 0
    #         for item in self.values():
    #             bits += item.unpack(buffer, bits)
    #         return index - bit_size_in_bytes(bits)
    #
    #     def size(self):
    #         if self.__size is None:
    #             return bit_size_in_bytes(super(MyBit, self).size())
    #         return self.__size



    data = ''.join(['%02x' % i for i in range(255)])
    header_data = data.decode("hex")

    #mb = MyBit()

    #mb.unpack('zbcd')
    #out = mb.pack()
    #print(out)
    hd = EncapsulationHeader()#.build_with_values(0,5,2,3,4,5,6,7,8,9,10,11,12,13,14)

    hd.unpack(header_data)
    v = hd.data
    d = hd.pack()
    print(d.encode('hex'))
    print(data)
    alt_struct = sub_alt.from_values(3, 5)
    hd.options = alt_struct
    hd.update()
    hd.length = 10
    hd.update()
    print(hd.get_format())
    hd.options.c = 0
    d = hd.pack()
    print(data)
    print(d.encode("hex"))
    print(hd)
    print(hd.__repr__())

    i=1
