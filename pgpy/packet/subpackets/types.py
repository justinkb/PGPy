""" subpacket.py
"""
import abc

from ...decorators import TypedProperty
from ...types import Dispatchable
from ...types import Header as _Header


class Header(_Header):
    @TypedProperty
    def critical(self):
        return self._critical
    @critical.bool
    def critical(self, val):
        self._critical = val
    @critical.bytearray
    @critical.bytes
    def critical(self, val):
        self._critical = bool(self.bytes_to_int(val) & 0x80)

    @TypedProperty
    def typeid(self):
        return self._typeid
    @typeid.bytearray
    @typeid.bytes
    def typeid(self, val):
        self._typeid = (self.bytes_to_int(val) & 0x7F)

    def parse(self, packet):
        self.length = packet
        del packet[:self.llen]

        self.critical = packet[:1]
        self.typeid = packet[:1]
        del packet[:1]

        return packet

    def __len__(self):
        return self.llen + 1

    def __bytes__(self):
        _bytes = self.encode_length(self.length)
        _bytes += self.int_to_bytes((int(self.critical) << 7) + self.typeid)
        return _bytes


class SubPacket(Dispatchable, metaclass=abc.ABCMeta):  ##TODO: is this metaclass declaration necessary?
    __headercls__ = Header

    def __init__(self):
        super(SubPacket, self).__init__()
        self.header = Header()

    def __bytes__(self):
        return self.header.__bytes__()

    def __len__(self):
        return (self.header.llen + self.header.length)

    def __repr__(self):
        return "<{} [0x{:02x}] at 0x{:x}>".format(self.__class__.__name__, self.header.typeid, id(self))

    @abc.abstractmethod  # subclasses still need to specify this
    def parse(self, packet):
        if self.header._typeid == 0:
            self.header.parse(packet)


class Signature(SubPacket):
    __typeid__ = -1


class UserAttribute(SubPacket):
    __typeid__ = -1


class Opaque(Signature, UserAttribute):
    __typeid__ = None

    @TypedProperty
    def payload(self):
        return self._payload
    @payload.bytearray
    @payload.bytes
    def payload(self, val):
        self._payload = val

    def __init__(self):
        super(Opaque, self).__init__()
        self.payload = b''

    def __bytes__(self):
        _bytes = super(Opaque, self).__bytes__()
        _bytes += self.payload
        return _bytes

    def parse(self, packet):
        super(Opaque, self).parse(packet)
        self.payload = packet[:(self.header.length - 1)]
        del packet[:(self.header.length - 1)]
