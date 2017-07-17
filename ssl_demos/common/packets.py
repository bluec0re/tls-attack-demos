from scapy.packet import Packet, bind_layers
from scapy.fields import *
try:
    from scapy.fields import ThreeBytesField
except ImportError:
    from scapy.fields import X3BytesField

    class ThreeBytesField(X3BytesField, ByteField):
        def i2repr(self, pkt, x):
            return ByteField.i2repr(self, pkt, x)

class TLSPacket(Packet):
    name = 'TLSPacket'
    fields_desc = [
            XByteField('content_type', None),
            ShortEnumField("version", 0x0303,
                {0x0301: "TLSv1.0", 0x0303: "TLSv1.2"}),
            ShortField("length", 0)
        ]


class TLSApplicationData(Packet):
    name = 'TLSApplicationData'


class TLSHandshake(Packet):
    name = 'TLSHandshake'
    fields_desc = [
            ByteEnumField('handshake_type', None, {
                1: 'Client Hello',
                2: 'Server Hello',
                11: 'Certificate',
                12: 'Server Key Exchange',
                14: 'Server Hello Done',
                16: 'Client Key Exchange',
            }),
            ThreeBytesField("length", None)
            ]


class TLSChangeCipherSpec(Packet):
    name = 'TLSChangeCipherSpec'


class TLSAlert(Packet):
    name = 'TLSAlert'


bind_layers(TLSPacket, TLSChangeCipherSpec, content_type=0x14)
bind_layers(TLSPacket, TLSAlert, content_type=0x15)
bind_layers(TLSPacket, TLSHandshake, content_type=0x16)
bind_layers(TLSPacket, TLSApplicationData, content_type=0x17)