import socket
from PyDynamicStructures import *
from enum import IntEnum

__all__ = ["octet_cip", "byte_cip", "bool_cip", "sint_cip", "int_cip", "dint_cip", "lint_cip", "usint_cip",
           "uint_cip", "udint_cip", "ulint_cip", "word_cip", "dword_cip", "lword_cip", "EPATH", "EItem", "EPATH_List",
           "short_string_cip", "string_cip", "string2_cip",
           "CommonServices", "SegmentType", "LogicalType", "LogicalFormat", "DataSubType"]

octet_cip   = BYTE_L
byte_cip    = BYTE_L
bool_cip    = BYTE_L
sint_cip    = INT8_L
int_cip     = INT16_L
dint_cip    = INT32_L
lint_cip    = INT64_L
usint_cip   = UINT8_L
uint_cip    = UINT16_L
udint_cip   = UINT32_L
ulint_cip   = UINT64_L
word_cip    = UINT16_L
dword_cip   = UINT32_L
lword_cip   = UINT64_L

class base_string_cip(DynamicClass):
    _encoding_size_ = 1
    _encoding_ = 'ISO-8859-1'
    _length_type_ = usint_cip

    def _getter_(self, *args):
        return self.value.decode(self._encoding_)

    def _setter_(self, instance, value):
        self.string_size = len(value)
        self.value = value.encode(self._encoding_)

    def structure(self):
        self.string_size = self._length_type_()
        self.value = RAW(length=self.string_size * self._encoding_size_)

    def __str__(self):
        return self._getter_()

    def __repr__(self):
        return self.__str__()

class short_string_cip(base_string_cip):
    _encoding_size_ = 1
    _encoding_ = 'ISO-8859-1'
    _length_type_ = usint_cip

class string_cip(base_string_cip):
    _encoding_size_ = 1
    _encoding_ = 'ISO-8859-1'
    _length_type_ = uint_cip

class string2_cip(base_string_cip):
    _encoding_size_ = 2
    _encoding_ = 'ISO-10646'
    _length_type_ = uint_cip

class CommonServices(IntEnum):
    get_all    = 0x01
    get_single = 0x0e

class SegmentType(IntEnum):

    PortSegment     = 0
    LogicalSegment  = 1
    NetworkSegment  = 2
    SymbolicSegment = 3
    DataSegment     = 4
    DataType_c      = 5
    DataType_e      = 6
    Reserved        = 7

class LogicalType(IntEnum):

    ClassID         = 0
    InstanceID      = 1
    MemberID        = 2
    ConnectionPoint = 3
    AttributeID     = 4
    Special         = 5
    ServiceID       = 6
    ExtendedLogical = 7

class LogicalFormat(IntEnum):

    bit_8    = 0
    bit_16   = 1
    bit_32   = 2
    Reserved = 3

class DataSubType(IntEnum):

    SimpleData = 0
    ANSI       = 9

class EHead(BitStructure):
    _low_first_ = False

    def structure(self):
        self.logical = BitElement(3)

        if self.logical == SegmentType.PortSegment:
            self.extended = BitElement(1)
            self.identifier = BitElement(4)

        elif self.logical == SegmentType.LogicalSegment:
            self.type = BitElement(3)
            self.format = BitElement(2)

        elif self.logical == SegmentType.NetworkSegment:
            self.sub_type = BitElement(5)

        elif self.logical == SegmentType.SymbolicSegment:
            self.sym_size = BitElement(5)

        elif self.logical == SegmentType.DataSegment:
            self.sub_type = BitElement(5)

        else:
            raise Exception('epath seg type not supported')

class EItem(DynamicClass):

    def structure(self):
        self.type = EHead()

        if self.type.logical == SegmentType.PortSegment:
            if self.type.identifier == 15:
                self.extended_port = UINT16()
            if self.type.extended:
                self.address_size = UINT8()
                self.link_address = UINT8() * self.address_size
            else:
                self.link_address = UINT8()

        elif self.type.logical == SegmentType.LogicalSegment:
            if self.type.type == LogicalType.ExtendedLogical:
                self.extended_logical = BYTE()
            if self.type.format == LogicalFormat.bit_8:
                self.value = UINT8_L()
            elif self.type.format == LogicalFormat.bit_16:
                self.value = UINT16_L()
            elif self.type.format == LogicalFormat.bit_132:
                self.value = UINT32_L()


class EPATH_List(DynamicList):

    def structure(self, size_path):
        max_size = self.get_variable(size_path)
        if max_size is not None:
            current_size = 0
            while current_size < max_size:
                self.append(EItem())
                current_size += self[-1].size()

            if max_size != current_size:
                raise Exception("EPATH Size mismatch should be %d not %d" % (self.size(), current_size))


# class EPATH_Selector(StructureSelector):
#     def structure(self):
#         size = self.get_variable(self.args[0])
#         epath = EPATH_List()
#         epath.set_size(size*2)
#         return epath


class EPATH(DynamicClass):
    def structure(self):
        self.epath_size = uint_cip()
        self.epath = EPATH_List('../epath_size')