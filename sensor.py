## Netwerken en Systeembeveiliging
## Lab 5 - Distributed Sensor Network
## Definitions and message format
import struct


class Message:
    """
    Made into a class for easy access to variables
    """

    def __init__(self):
        ## These are the message types.
        self.MSG_PING = 0  # Multicast ping.
        self.MSG_PONG = 1  # Unicast pong.
        self.MSG_ECHO = 2  # Unicast echo.
        self.MSG_ECHO_REPLY = 3  # Unicast echo reply.

        ## These are the echo operations.
        self.OP_NOOP = 0  # Do nothing.
        self.OP_SIZE = 1  # Compute the size of network.
        self.OP_SUM = 2  # Compute the sum of all sensor values.
        self.OP_MIN = 3  # Compute the lowest sensor value.
        self.OP_MAX = 4  # Compute the highest sensor value.
        self.OP_SAME = 5  # Compute the number of sensors with the same value.

        ## This is used to pack message fields into a binary format.
        self.message_format = struct.Struct('!8if')

        ## Length of a message in bytes.
        self.message_length = self.message_format.size

    def message_encode(self, type, sequence, initiator, neighbor, operation=0, capability=0, payload=0):
        """
        Encodes message fields into a binary format.
        type: The message type.
        sequence: The wave sequence number.
        initiator: An (x, y) tuple that contains the initiator's position.
        neighbor: An (x, y) tuple that contains the neighbor's position.
        operation: The echo operation.
        capability: The capability range of initiator
        payload: Echo operation data (a number).
        Returns: A binary string in which all parameters are packed.
        """
        ix, iy = initiator
        nx, ny = neighbor
        return self.message_format.pack(type, sequence,
                                        ix, iy, nx, ny, operation, capability, payload)

    def message_decode(self, buffer):
        """
        Decodes a binary message string to Python objects.
        buffer: The binary string to decode.
        Returns: A tuple containing all the unpacked message fields.
        """
        type, sequence, ix, iy, nx, ny, operation, capability, payload = \
            self.message_format.unpack(buffer)
        return (type, sequence, (ix, iy), (nx, ny), operation, capability, payload)
