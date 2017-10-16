import socket
from PyDynamicStructures import *
from ctypes import Structure, c_uint16, c_uint32, c_uint64, addressof, memmove, create_string_buffer
from enum import IntEnum
from Examples.cip_types import EPATH, EPATH_Selector, EItem, SegmentType, LogicalFormat, LogicalType


class ENIPCommandCode(IntEnum):

    NOP               = 0x00
    ListServices      = 0x04
    ListIdentity      = 0x63
    ListInterfaces    = 0x64
    RegisterSession   = 0x65
    UnRegisterSession = 0x66
    SendRRData        = 0x6f
    SendUnitData      = 0x70

class CPFType(IntEnum):

    Null               = 0x00
    ConnectedAddress   = 0xa1
    SequencedAddress   = 0x8002
    UnconnectedData    = 0xb2
    ConnectedData      = 0xb1
    SockaddrInfo_OT    = 0x8000
    SockaddrInfo_TO    = 0x8001


class CommandSpecificBase(StructureClass):
    COMMAND_CODE = None

class Nop(CommandSpecificBase):
    COMMAND_CODE = ENIPCommandCode.NOP
    def structure(self):
        pass

class RegisterSession(CommandSpecificBase):
    COMMAND_CODE = ENIPCommandCode.RegisterSession
    def structure(self):
        self.protocol_version = UINT16_L()
        self.options_flags    = UINT16_L()

class UNRegisterSession(CommandSpecificBase):
    COMMAND_CODE = ENIPCommandCode.UnRegisterSession
    def structure(self):
        pass

class SendRRData(CommandSpecificBase):
    COMMAND_CODE = ENIPCommandCode.SendRRData
    def structure(self):
        self.interface_handle = UINT32_L()
        self.timeout          = UINT16_L()
        self.cpf              = CPF()

class SendUnitData(CommandSpecificBase):
    COMMAND_CODE = ENIPCommandCode.SendUnitData
    def structure(self):
        self.interface_handle = UINT32_L()
        self.timeout          = UINT16_L()
        self.cpf              = CPF()

class CommandSpecificSelector(StructureSelector):
    CS_STRUCTS = {cs.COMMAND_CODE: cs for cs in CommandSpecificBase.__subclasses__()}

    def structure(self):
        command = self.get_variable(self.kwargs['command'])
        size    = self.get_variable(self.kwargs['size'])
        struct  = self.CS_STRUCTS.get(command)

        if struct is None:
            raise Exception('Command code unsupported')
        if size > 65511:
            raise Exception('packet length to long')

        instance  = struct()
        instance.set_size(size)
        return instance

class ENIPEncapsulationHeader(StructureClass):
    def structure(self):
        self.command           = UINT16_L()
        self.length            = UINT16_L()
        self.session_handle    = UINT32_L()
        self.status            = UINT32_L()
        self.sender_context    = UINT64_L()
        self.options           = UINT32_L()
        self.command_specific  = EMPTY()

class ENIPEncapsulationPacket(StructureClass):
    def structure(self):
        self.command           = UINT16_L()
        self.length            = UINT16_L()
        self.session_handle    = UINT32_L()
        self.status            = UINT32_L()
        self.sender_context    = UINT64_L()
        self.options           = UINT32_L()
        self.command_specific  = CommandSpecificSelector(command='../command', size='../length')

class CPF_Item(DynamicClass):
    def structure(self):
        self.type_id = UINT16_L()
        self.length  = UINT16_L()

        if self.type_id == CPFType.Null:
            pass

        elif self.type_id == CPFType.ConnectedAddress:
            if self.length != 4:
                raise Exception("CPF Connected addr length should be 4 not %d" % self.length)
            self.connection_identifier = UINT32_L()

        elif self.type_id == CPFType.SequencedAddress:
            if self.length != 8:
                raise Exception("CPF SequencedAddress length should be 8 not %d" % self.length)
            self.connection_identifier = UINT32_L()
            self.sequence_number = UINT32_L()

        elif self.type_id == CPFType.UnconnectedData:
            self.data = RAW(length=self.length)

        elif self.type_id == CPFType.ConnectedData:
            self.data = RAW(length=self.length)

        elif self.type_id in (CPFType.SockaddrInfo_OT, CPFType.SockaddrInfo_TO):
            if self.length != 16:
                raise Exception("CPF SockaddrInfo length should be 16 not %d" % self.length)
            self.sin_family = INT16_L()
            self.sin_port   = UINT16_L()
            self.sin_addr   = UINT32_L()
            self.sin_zero   = UINT8_L() * 8

        else:
            raise Exception("CPF type not supported %x" % self.type_id)


class CPF(StructureClass):
    def structure(self):
        self.item_count = UINT16_L()
        self.item = Array(length_path='../item_count', type=CPF_Item)


class ENIP(object):

    def __init__(self, ip_address, port=0xAF12):

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((ip_address, port))

        self.internal_sender_context = 10
        self.session_handle          = None
        self.packets                 = dict()

        sender_context = self.register_session()
        packet         = self.read(sender_context, True)

        self.session_handle  = packet.session_handle


    def register_session(self):
        self.internal_sender_context += 1

        command_specific = RegisterSession(protocol_version=1, options_flags=0)

        encap_header = ENIPEncapsulationPacket(command=ENIPCommandCode.RegisterSession,
                                               length=sizeof(command_specific),
                                               session_handle=0,
                                               status=0,
                                               sender_context=self.internal_sender_context,
                                               options=0,
                                               )
        encap_header.command_specific = command_specific

        data = encap_header.pack()
        self.sock.sendall(data)

        return self.internal_sender_context

    def send_enip(self, message):
        self.internal_sender_context += 1

        cpf = CPF(item_count=2)
        cpf.item[0] = CPF_Item(type_id=CPFType.Null, length=0)
        cpf.item[1] = CPF_Item(type_id=CPFType.UnconnectedData, length=len(message))
        cpf.item[1].data = message

        command_specific = SendRRData(0, 0)
        command_specific.cpf = cpf

        encap_header = ENIPEncapsulationPacket(command=ENIPCommandCode.SendRRData,
                                               length=sizeof(command_specific),
                                               session_handle=self.session_handle,
                                               status=0,
                                               sender_context=self.internal_sender_context,
                                               options=0,
                                               )

        encap_header.command_specific = command_specific

        self.sock.sendall(encap_header.pack())

        return self.internal_sender_context


    def read(self, sender_context=None, full_packet=False):

        if sender_context is not None and sender_context in self.packets:
            return self.packets[sender_context]

        encap_packet = ENIPEncapsulationHeader()
        payload = self.sock.recv(sizeof(encap_packet))
        encap_packet.unpack(payload)
        payload += self.sock.recv(encap_packet.length)

        encap_packet = ENIPEncapsulationPacket()
        encap_packet.unpack(payload)


        if encap_packet.sender_context != 0:
            self.packets[encap_packet.sender_context] = encap_packet

        if full_packet:
            return encap_packet
        return encap_packet.command_specific.cpf.item[1].data


class MessageRouter(StructureClass):
    def structure(self):
        self.service = UINT8()
        self.path_size = UINT8()
        self.epath = EPATH_Selector('../path_size')
        self.data  = RAW_END()

class MessageRouterResponce(StructureClass):
    def structure(self):
        self.service = UINT8()
        self.reserved = UINT8()
        self.general_status = UINT8()
        self.additional_size = UINT8()
        self.additional_status = Array(length_path='../additional_size', type=UINT16)
        self.data = RAW_END()


class CIP(object):

    def __init__(self, ip_address, port=0xAF12):
        self.enip = ENIP(ip_address, port)


    def send_encap(self, service, class_id=None, instance_id=None, attribute_id=None, data=None, route=None):

        message = MessageRouter()
        message.service = service
        if class_id is not None:
            message.epath.append(EItem(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, class_id))
        if instance_id is not None:
            message.epath.append(EItem(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, instance_id))
        if attribute_id is not None:
            message.epath.append(EItem(SegmentType.LogicalSegment, LogicalType.AttributeID, LogicalFormat.bit_8, attribute_id))
        if data is not None:
            message.data = data

        message.path_size = message.epath.struct_size() // 2

        receipt = self.enip.send_enip(message.pack())
        rsp = self.enip.read(receipt)
        rsp_struct = MessageRouterResponce()
        rsp_struct.unpack(rsp)

        if rsp_struct.general_status != 0:
            raise Exception('CIP ERROR general status %d' % rsp_struct.general_status)
        return rsp_struct.data

class EmbeddedMessageSelector(StructureSelector):
    def structure(self):
        size = self.get_variable(self.kwargs['request_size'])
        message = MessageRouter()
        message.set_size(size)
        return message

class ConnectionManager(StructureClass):
    def structure(self):
        self.priority = UINT8()
        self.ticks = UINT8()
        self.request_size = UINT16_L()
        self.message_request = EmbeddedMessageSelector(request_size='../request_size')
        self.pad = PADD()
        self.route_size = UINT8()
        self.reserved = UINT8()
        self.route_path = EPATH_Selector('../request_size')

if __name__ == '__main__':
    # from psttools.utils.bootp import BootpServer
    # bp = BootpServer()
    # bp.set_device('00-A0-EC-44-9B-2E', "192.168.0.15", '255.255.255.0')
    # bp.start()

    con = CIP("192.168.0.25")
    print(con.send_encap(0x0e, 1, 1, 7))
    cm = ConnectionManager(priority=100,
                            ticks=100)

    cm.message_request.service = 0x0e
    cm.message_request.epath.append(EItem(SegmentType.LogicalSegment, LogicalType.ClassID, LogicalFormat.bit_8, 1))
    cm.message_request.epath.append(EItem(SegmentType.LogicalSegment, LogicalType.InstanceID, LogicalFormat.bit_8, 1))
    cm.message_request.epath.append(EItem(SegmentType.LogicalSegment, LogicalType.AttributeID, LogicalFormat.bit_8, 7))
    cm.message_request.path_size = cm.message_request.epath.struct_size() // 2
    cm.request_size = cm.message_request.struct_size()

    cm.route_path.append(EItem(SegmentType.PortSegment, 0, 1, 0))
    cm.route_size = cm.route_path.struct_size() // 2

    rsp = con.send_encap(0x52, 6, 1, data=cm.pack())





    # bp.stop()
