from __future__ import print_function
import struct
import GP9DataFormat

class GP9Packet(object):
    """Defines a GP9Packet and reading functions

    Keyword Arguments
    -----------------
    header: decode only a packet header
    full_packet: decode a full packet
    
    Public Member Variables:
    ------------------------
    raw_bytes
    header
        address
        has_data
        is_batch
        batch_length
        hidden
        command_failed
    data
        data_length
    checksum
        checksum_good
    """

    # Valid kwargs are 'header', 'full_packet'
    def __init__(self, **kwargs):
        # Clear all the member variables
        self.header = ''
        self.data = ''
        self.raw_data = ''
        self.checksum = ''
        # Checksum includes the start bytes
        self.raw_bytes = [ord(c) for c in 'snp']
        self.checksum_good = False

        if 'header' in kwargs:
            self.decode_header(kwargs['header'])

        # Use for testing with full packet at once
        if 'full_packet' in kwargs:
            self.ingest_packet(kwargs['full_packet'])

    def ingest_packet(self, packet):
        self.decode_header(packet[3:5])
        if self.has_data:
            self.set_data(packet[5:-2])
        self.set_checksum(packet[-2:])

    def decode_header(self, header_bytes):
        if self.header == '':
            self.header = header_bytes

        split_bytes = struct.unpack('>2B', header_bytes)
        # Keep a running tally of bytes for the checksum
        self.raw_bytes.extend(list(split_bytes))

        packet_type = split_bytes[0]
        self.address = split_bytes[1]

        # Split the Packet Type
        self.has_data = (((packet_type & 0b10000000) >> 7) == 1)
        self.is_batch = (((packet_type & 0b01000000) >> 6) == 1)
        self.batch_length = (packet_type & 0b00111100) >> 2
        self.hidden = (((packet_type & 0b00000010) >> 1) == 1)
        self.command_failed = ((packet_type & 0b00000001) == 1)

        # Determine data length
        # 4 times the batch length, or 4 bytes
        self.data_length = 4 * self.batch_length if self.is_batch else 4

        return self.data_length

    def set_data(self, data):
        # Leave this raw for later decoding
        self.raw_data = data

        # Add to the checksum calc
        data_format = '>' + str(self.data_length) + 'B'
        split_bytes = struct.unpack(data_format, data)
        self.raw_bytes.extend(list(split_bytes))

    def decode_data(self):
        self.data = DataDecoder.decode(self)

    def set_checksum(self, checksum):
        self.checksum = struct.unpack('>H', checksum)[0]
        self.verify_checksum()

    def verify_checksum(self):
        if self.checksum != '':
            self.checksum_good = (sum(self.raw_bytes) == self.checksum)

        return self.checksum_good

    def print_packet_info(self):
        pass


class DataDecoder(object):
    """Decodes data from the GP9 based on packet address
    """
    def __init__(self, packet):
        self.raw_data = packet.data
        self.address = packet.address
        self.data = self.decode(packet)

    @staticmethod
    def decode(packet):
        if packet.checksum_good:
            if packet.has_data:
                # Check through known packet types
                if packet.address == 120:
                    data = GP9DataFormat.Data120(packet.raw_data)
                elif packet.address == 86 and packet.batch_length == 14:
                    #Decode first part
                    data = GP9DataFormat.Data86(packet.raw_data[0:12])
                elif packet.address == 86 and packet.batch_length == 3:
                    data = GP9DataFormat.Data86(packet.raw_data)
                elif packet.address == 1:
                    data = GP9DataFormat.Config1(packet.raw_data)
                elif packet.address == 2:
                    data = GP9DataFormat.Config2(packet.raw_data)
                elif packet.address == 3:
                    data = GP9DataFormat.Config3(packet.raw_data)
                elif packet.address == 4:
                    data = GP9DataFormat.Config4(packet.raw_data)
                elif packet.address == 5:
                    data = GP9DataFormat.Config5(packet.raw_data)
                elif packet.address == 6:
                    data = GP9DataFormat.Config6(packet.raw_data)
                else:
                    data = None
                    print('Unrecognized packet type.')
                return data
            else:
                return GP9DataFormat.CommandResponse(packet.address, not packet.command_failed)
        else:
            print('Can\'t process data with bad checksum.')
