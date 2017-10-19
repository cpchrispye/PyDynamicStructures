import socket

from enum import IntEnum

from PyDynamicStructures import *
from cip_types import *
from enip import ENIP
import re

class MessageRouter(StructureClass):
    def structure(self):
        self.service = UINT8()
        self.path_size = UINT8()
        self.epath = EPATH_List('../path_size')
        self.data  = RAW_END()

class MessageRouterResponce(StructureClass):
    def structure(self):
        self.service = UINT8()
        self.reserved = UINT8()
        self.general_status = UINT8()
        self.additional_size = UINT8()
        self.additional_status = Array('../additional_size', UINT16)
        self.data = RAW_END()

class EmbeddedMessageSelector(StructureSelector):
    def structure(self, request_size):
        size = self.get_variable(request_size)
        message = MessageRouter()
        message.set_size(size)
        return message

class ConnectionManager(DynamicClass):
    def structure(self):
        self.priority = UINT8()
        self.ticks = UINT8()
        self.request_size = UINT16_L()
        self.message_request = EmbeddedMessageSelector('../request_size')
        if self.size() % 2:
            self.pad = PADD()
        self.route_size = UINT8()
        self.reserved = UINT8()
        self.route_path = EPATH_List('../route_size')


def build_ucmm_message(service, class_id=None, instance_id=None, attribute_id=None, data=None):
    message = MessageRouter()
    message.service = service
    if class_id is not None:
        message.epath.append(EItem.from_values(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, class_id))
    if instance_id is not None:
        message.epath.append(EItem.from_values(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, instance_id))
    if attribute_id is not None:
        message.epath.append(EItem.from_values(SegmentType.LogicalSegment, LogicalType.AttributeID, LogicalFormat.bit_8, attribute_id))

    if data is not None:
        message.data = data

    message.path_size = message.epath.struct_size() // 2
    return message


class CIP(object):

    def __init__(self, path, port=0xAF12):
        items = path.split('/')
        ip_address = items.pop(0)

        self.route = []
        while len(items) >= 2:
            self.route.append(items[:2])
            items = items[2:]

        self.enip = ENIP(ip_address, port)

    def send_encap(self, service, epath_list, data=None):
        if self.route:
            cm = ConnectionManager.from_values(priority=100,
                                               ticks=100)

            cm.message_request.service = service
            cm.message_request.epath = StructureList(epath_list)
            cm.message_request.path_size = cm.message_request.epath.struct_size() // 2
            if data is not None:
                cm.message_request.data = data
            cm.request_size = cm.message_request.struct_size()

            for port in self.route:
                cm.route_path.append(EItem.from_values(SegmentType.PortSegment, 0, int(port[0]), int(port[1])))
            cm.route_size = cm.route_path.struct_size() // 2

            message = build_ucmm_message(0x52, 6, 1, data=cm)
        else:
            message = MessageRouter()
            message.service = service
            message.epath = StructureList(epath_list)
            message.path_size = message.epath.struct_size() // 2
            if data is not None:
                message.data = data

        receipt = self.enip.send_enip(message.pack())
        rsp = self.enip.read(receipt)
        rsp_struct = MessageRouterResponce()
        rsp_struct.unpack(rsp)

        if rsp_struct.general_status != 0:
            raise Exception('CIP ERROR general status %d' % rsp_struct.general_status)
        return rsp_struct.data

    def send_class_encap(self, service, class_id=None, instance_id=None, attribute_id=None, data=None):
        epath = list()
        if class_id is not None:
            epath.append(
                EItem.from_values(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, class_id))
        if instance_id is not None:
            epath.append(
                EItem.from_values(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, instance_id))
        if attribute_id is not None:
            epath.append(
                EItem.from_values(SegmentType.LogicalSegment, LogicalType.AttributeID, LogicalFormat.bit_8,
                                  attribute_id))

        return self.send_encap(service, epath, data)

    def get_variable(self, name, qty=1):
        attribute_names = name.split('.')
        epath = []
        for name in attribute_names:
            arrayed = name.split('[')
            name = arrayed[0]
            epath.append(EItem.from_values(SegmentType.DataSegment, 0x11, name))
            for index in arrayed[1:]:
                index = index.replace(']', '')
                index = int(index)
                epath.append(EItem.from_values(SegmentType.LogicalSegment, LogicalType.MemberID, LogicalFormat.bit_8, index))

        size = uint_cip(qty)
        rsp = self.send_encap(0x4c, epath, size)
        val = VariableResponse.from_buffer(rsp)
        return val.value


class VariableSelector(StructureSelector):
    DATATYPES = {
        0xC1: bool_cip,
        0xC2: sint_cip,
        0xC3: int_cip,
        0xC4: dint_cip,
        0xC5: lint_cip,

        0xC6: usint_cip,
        0xC7: uint_cip,
        0xC8: udint_cip,
        0xC9: ulint_cip,

        0xCA: FLOAT_L,
        0xCB: DOUBLE_L,

        0xD1: byte_cip,
        0xD2: word_cip,
        0xD3: dword_cip,
        0xD4: lword_cip,
    }

    def structure(self, data_type_path):
        data_type = self.get_variable(data_type_path)
        obj = self.DATATYPES.get(data_type, 0)
        if obj == 0:
            return EMPTY()
        return obj()

class VariableResponse(StructureClass):
    def structure(self):
        self.data_type = uint_cip()
        self.value = VariableSelector('../data_type')


class IndentiyObject(StructureClass):
    def structure(self):
        self.vendor_id = UINT16_L()
        self.device_type = UINT16_L()
        self.product_code = UINT16_L()
        self.major_rev = UINT8_L()
        self.minor_rev = UINT8_L()
        self.status = UINT16_L()
        self.serial_number = UINT32_L()
        self.product_name = short_string_cip()



if __name__ == '__main__':

    id = IndentiyObject()

    con = CIP("192.168.0.115")
    rsp = con.send_class_encap(CommonServices.get_all, 1, 1)
    id = IndentiyObject.from_buffer(rsp)
    print(id.product_name)

    #val = con.get_variable('Local:5:O.Ch[0].Data')

    i=1
