import struct

class PacketConstructor(object):
    """Builds a GP9 Packet from the provided data

    Keyword arguments
    -----------------
    data: A GP9DataFormat object with data to write
    read: An address to generate a read request
    """
    def __init__(self, **kwargs):
        self.ready_to_send = False
        self.packet = None
        if 'data' in kwargs:
            self.gen_write(kwargs['data'])
        elif 'read' in kwargs:
            self.gen_read_request(kwargs['read'])

    def gen_write(self, data_format):
        # packet type
        if data_format.has_data:
            packet_type = 0b10000000
        else:
            packet_type = 0

        if data_format.is_batch:
            packet_type = packet_type | (1 << 6)
            packet_type = packet_type | (data_format.batch_len << 2)

        self.gen_packet(packet_type, data_format.address, data_format.raw_data)

    def gen_read_request(self, address, is_batch=False, batch_len=0):
        packet_type = 0
        if is_batch:
            packet_type = packet_type | (1 << 6)
            packet_type = packet_type | batch_len << 2
        self.gen_packet(packet_type, address, None)

    def gen_packet(self, packet_type, address, data):
        # packet start
        self.packet = struct.pack('>3B', ord('s'), ord('n'), ord('p'))
        self.packet = self.packet + struct.pack('>2B', packet_type, address)
        # data
        if data is not None:
            self.packet = self.packet + data

        # generate checksum
        all_bytes = struct.unpack('>' + str(len(self.packet)) + 'B', self.packet)
        checksum = sum(all_bytes)
        self.packet = self.packet + struct.pack('>H', checksum)

        self.ready_to_send = True
