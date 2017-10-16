import socket
from PyDynamicStructures import *
from enum import IntEnum

__all__ = ["octet_cip", "byte_cip", "bool_cip", "sint_cip", "int_cip", "dint_cip", "lint_cip", "usint_cip", "uint_cip", "udint_cip", "ulint_cip", "word_cip", "dword_cip", "lword_cip", "EPATH", "EPATH_Selector"]

octet_cip   =BYTE
byte_cip    =BYTE
bool_cip    =BYTE
sint_cip    =INT8
int_cip     =INT16
dint_cip    =INT32
lint_cip    =INT64
usint_cip   =UINT8
uint_cip    =UINT16
udint_cip   =UINT32
ulint_cip   =UINT64
word_cip    =UINT16
dword_cip   =UINT32
lword_cip   =UINT64

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
    def structure(self):
        my_size = 0
        while self.size() > my_size:
            self.append(EItem())
            my_size += self[-1].size()

        if self.size() != my_size:
            raise Exception("EPATH Size mismatch should be %d not %d" % (self.size(), my_size))


class EPATH_Selector(StructureSelector):
    def structure(self):
        size = self.get_variable(self.args[0])
        epath = EPATH_List()
        epath.set_size(size*2)
        return epath


class EPATH(DynamicClass):
    def structure(self):
        self.epath_size = uint_cip()
        self.epath = EPATH_Selector('../epath_size')