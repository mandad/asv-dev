import struct
import GP9DataFormat

class PacketConstructor(object):
    """Builds a GP9 Packet from the provided data
    """
    def __init__(self, data_format):
        self.data_format = data_format
        self.ready_to_send = False
        self.packet = None
        self.gen_packet()

    def gen_packet(self):
        # packet start
        self.packet = struct.pack('>3B', ord('s'), ord('n'), ord('p'))

        # packet type
        if self.data_format.has_data:
            packet_type = 0b10000000
        else:
            packet_type = 0

        if self.data_format.is_batch:
            packet_type = packet_type | (1 << 6)
            packet_type = packet_type | self.data_format.batch_len << 2
        self.packet = self.packet + struct.pack('>B', packet_type)

        # address
        self.packet = self.packet + struct.pack('>B', self.data_format.address)

        # data
        self.packet = self.packet + self.data_format.raw_data

        # generate checksum
        all_bytes = struct.unpack('>' + str(len(self.packet)) + 'B', self.packet)
        checksum = sum(all_bytes)
        self.packet = self.packet + struct.pack('>H', checksum)

        self.ready_to_send = True
