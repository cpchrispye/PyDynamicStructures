import socket
from PyDynamicStructures import *
from ctypes import Structure, c_uint16, c_uint32, c_uint64, addressof, memmove, create_string_buffer
from enum import IntEnum

class EncapPacketStructure(object):

    def __init__(self):
        self.header
        self.command_specific
        self.cpf
        self.data





class ENIPCommandCode(IntEnum):

    NOP               = 0x00
    ListServices      = 0x04
    ListIdentity      = 0x63
    ListInterfaces    = 0x64
    RegisterSession   = 0x65
    UnRegisterSession = 0x66
    SendRRData        = 0x6f
    SendUnitData      = 0x70


class NetworkStructure(Structure):
    _pack_ = 1

    def unpack(self):
        buffer = create_string_buffer(sizeof(self))
        memmove(buffer, addressof(self), sizeof(self))
        return buffer.raw

    def pack(self, data):
        memmove(addressof(self), data, sizeof(self))


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

class SendUnitData(CommandSpecificBase):
    COMMAND_CODE = ENIPCommandCode.SendUnitData
    def structure(self):
        self.interface_handle = UINT32_L()
        self.timeout          = UINT16_L()

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
        self.command_specific  = CommandSpecificSelector(command='../command', size='../length')

class CPF_Unconnected(NetworkStructure):

    _fields_ = [
        ("type_id", c_uint16),
        ("length",  c_uint16),
    ]


def parse_enip_packet(header, packet):

    if header.command == ENIPCommandCode.RegisterSession:
        command_specific = RegisterSession()

    elif header.command == ENIPCommandCode.SendRRData:
        command_specific = SendRRData()

    command_specific.unpack(packet)
    return command_specific


class ENIP(object):

    def __init__(self, ip_address, port=0xAF12):

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((ip_address, port))

        self.internal_sender_context = 10
        self.session_handle          = None
        self.packets                 = dict()

        sender_context = self.register_session()
        packet         = self.read(sender_context)

        self.session_handle  = packet.session_handle


    def register_session(self):
        self.internal_sender_context += 1

        command_specific = RegisterSession(protocol_version=1, options_flags=0)

        encap_header = ENIPEncapsulationHeader(ENIPCommandCode.RegisterSession,
                                               sizeof(command_specific),
                                               0,
                                               0,
                                               self.internal_sender_context,
                                               0,
                                               )
        encap_header.command_specific = command_specific

        data = encap_header.pack()
        self.sock.sendall(data)

        return self.internal_sender_context

    def send_enip(self, message):
        self.internal_sender_context += 1

        cpf = CPF_Unconnected(0xB2, sizeof(message))

        command_specific = SendRRData(0, 0)

        encap_header = ENIPEncapsulationHeader(ENIPCommandCode.SendRRData,
                                               sizeof(command_specific) + sizeof(cpf) + cpf.length,
                                               self.session_handle,
                                               0,
                                               self.internal_sender_context,
                                               0,
                                               )


        self.sock.sendall(encap_header.unpack() + command_specific.unpack() + cpf.unpack() + message.unpack())

        return self.internal_sender_context


    def read(self, sender_context=None):

        if sender_context is not None and sender_context in self.packets:
            return self.packets[sender_context]

        header = ENIPEncapsulationHeader()

        data_size = self.sock.recv_into(header, sizeof(header))

        payload = self.sock.recv(header.length)

        encap_packet = parse_enip_packet(header, payload)

        if header.sender_context != 0:
            self.packets[header.sender_context] = encap_packet

        if sender_context is not None:
            return self.packets[sender_context]
        else:
            return encap_packet


class CIP(object):

    def __init__(self, ip_address, port=0xAF12):
        self.enip = ENIP(ip_address, port)


    def send_cip(self, service, class_id, instance_id, data, route=None):
        pass


if __name__ == '__main__':
    # from psttools.utils.bootp import BootpServer
    # bp = BootpServer()
    # bp.set_device('00-A0-EC-44-9B-2E', "192.168.0.15", '255.255.255.0')
    # bp.start()

    con = CIP("192.168.0.25")
    i = 1

    # bp.stop()
