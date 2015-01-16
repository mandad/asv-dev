import struct
import GP9_packet

def gen_packet(address, data, is_batch = False, batch_len = 1):
    # packet start
    packet = struct.pack('>3B', ord('s'), ord('n'), ord('p'))

    # packet type
    pt = 0b10000000 #Has data
    if is_batch:
        pt = pt | (1 << 6)
        pt = pt | batch_len << 2
    packet = packet + struct.pack('>B', pt)

    # address
    packet = packet + struct.pack('>B', address)

    # data
    for item in data:
        packet = packet + struct.pack('>' + item[0], item[1])

    # generate checksum
    all_bytes = struct.unpack('>' + str(len(packet)) + 'B', packet)
    checksum = sum(all_bytes)
    packet = packet + struct.pack('>H', checksum)

    return packet


def gen_test_packet():
    data = [('h', 5215.18917), ('h', 1000), ('h', -5215.18917), ('h', 0), ('f', 3.5e5)]
    address = 0x78 # 120 - Euler Angles
    return gen_packet(address, data, True, 3)


def main():
    pass


if __name__ == '__main__':
    main()