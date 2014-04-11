from pysocketio_parser.util import try_convert

from pyemitter import Emitter
import json
import logging

log = logging.getLogger(__name__)


# Protocol version
PROTOCOL = 3

# Packet types.
TYPES = [
    'CONNECT',
    'DISCONNECT',
    'EVENT',
    'BINARY_EVENT',
    'ACK',
    'ERROR'
]

# Packet type `connect`.
CONNECT = 0

# Packet type `disconnect`.
DISCONNECT = 1

# Packet type `event`.
EVENT = 2

# Packet type `ack`.
ACK = 3

# Packet type `error`.
ERROR = 4

# Packet type `binary event`
BINARY_EVENT = 5


class Encoder(object):
    def __init__(self):
        """A socket.io Encoder instance"""
        pass

    @classmethod
    def encode(cls, obj, callback):
        """Encode a packet as a single string if non-binary, or as a
           buffer sequence, depending on packet type.

        :param obj: packet
        :type obj: dict

        :param callback: function to handle encodings (likely engine.write)
        :type callback: function

        :return: Calls callback with list of encodings
        """
        log.debug('encoding packet %s', obj)

        p_type = obj['type']

        if p_type in [BINARY_EVENT, ACK]:
            cls.binary_encode(obj, callback)
        else:
            encoding = cls.string_encode(obj)
            callback([encoding])

    @staticmethod
    def string_encode(obj):
        """Encode packet as string.

        :param obj: packet
        :type obj: dict

        :return: encoded packet
        :rtype: str
        """
        result = ''
        nsp = False

        # first is type
        result += str(obj['type'])

        # attachments if we have them
        if obj['type'] in [BINARY_EVENT, ACK]:
            result += obj.get('attachments', '')
            result += '-'

        # if we have a namespace other than `/`
        # we append it followed by a comma `,`
        if obj.get('nsp') and obj['nsp'] != '/':
            nsp = True
            result += obj['nsp']

        # immediately followed by the id
        if obj.get('id'):
            if nsp:
                result += ','
                nsp = False

            result += str(obj['id'])

        # json data
        if obj.get('data'):
            if nsp:
                result += ','

            result += json.dumps(obj['data'])

        log.debug('encoded %s as %s', obj, result)
        return result

    @staticmethod
    def binary_encode(obj, callback):
        """Encode packet as 'buffer sequence' by removing blobs, and
           deconstructing packet into object with placeholders and
           a list of buffers.

        :param obj: packet
        :type obj: dict

        :return: encoded
        :rtype: bytearray
        """
        pass


class Decoder(Emitter):
    def __init__(self):
        """A socket.io Decoder instance"""
        pass

    def add(self, obj):
        """Decodes an ecoded packet string into packet JSON.

        :param obj: encoded packet
        :type obj: str

        :return packet
        :rtype: dict
        """
        packet = None

        if isinstance(obj, basestring):
            packet = string_decode(obj)
            log.debug('string_decode packet: %s', packet)

            if packet['type'] in [BINARY_EVENT, ACK]:
                raise NotImplementedError()
            else:
                self.emit('decoded', packet)
        else:
            raise NotImplementedError()

    def destroy(self):
        """Deallocates a parser's resources"""
        pass


def string_decode(string):
    """Decode a packet String (JSON data)

    :param string: encoded packet string
    :type string: str

    :return: packet
    :rtype: dict
    """
    p = {}
    i = 0

    # look up type
    p['type'] = try_convert(string[0], int)

    if p['type'] is None or p['type'] >= len(TYPES):
        return error()

    # look up attachments if type binary
    if p['type'] in [BINARY_EVENT, ACK]:
        p['attachments'] = ''

        while string[i] != '-':
            i += 1
            p['attachments'] += string[i]

        p['attachments'] = try_convert(p['attachments'], int)

    # look up namespace (if any)
    if string[i + 1] == '/':
        p['nsp'] = ''

        while i + 1 < len(string):
            i += 1

            c = string[i]

            if c == ',':
                break

            p['nsp'] += c
    else:
        p['nsp'] = '/'

    # look up id
    next = string[i + 1] if i + 1 < len(string) else None

    if next and try_convert(next, int):
        p['id'] = ''

        while i + 1 < len(string):
            i += 1

            c = string[i]

            if not c or not try_convert(c, int):
                i -= 1
                break

            p['id'] += string[i]

        p['id'] = try_convert(p['id'], int)

    # look up json data
    if string[i + 1:]:
        try:
            p['data'] = json.loads(string[i + 1:])
        except:
            return error()

    log.debug('decoded %s as %s', string, p)
    return p


class BinaryReconstructor(object):
    def __init__(self, packet):
        """A manager of a binary event's 'buffer sequence'. Should
           be constructed whenever a packet of type BINARY_EVENT is
           decoded.

        :param packet: packet
        :type packet: dict
        """
        pass

    def take_binary_data(self, bin_data):
        """Method to be called when binary data received from connection
           after a BINARY_EVENT packet.

        :param bin_data: the raw binary data received
        :type bin_data: bytearray

        :return: returns None if more binary data is expected or a
                 reconstructed packet object if all buffers have
                 been received
        :rtype: None or dict
        """
        pass

    def finished_reconstruction(self):
        """Cleans up binary packet reconstruction variables."""
        pass


def error(data=None):
    return {
        'type': ERROR,
        'data': data or 'parser error'
    }
