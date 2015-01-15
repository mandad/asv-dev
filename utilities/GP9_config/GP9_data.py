import serial
import struct
import GP9_packet
#from __future__ import print_function

def main():
    ser = serial.Serial('/dev/ttyO2', 115200, timeout=10)
    byte_hist = [0,0,0]
    if ser.isOpen:
        try:
             while True:
                #find start of packet
                read_byte = ser.read(1)
                #read_up = struct.unpack('<B', read_byte)
                byte_hist.pop()
                byte_hist.insert(0, read_byte)

                if byte_hist == ['p', 'n', 's']:
                    #Have start of packet, read it in
                    header_bytes = ser.read(2)
                    data_length = decode_header(header)
                    data = ser.read(data_length)
                    checksum = ser.read(2)

         except (KeyboardInterrupt, SystemExit):
             ser.close()
             break

def decode_header(header_bytes):
    split_bytes = struct.unpack('<2B');
    packet_type = split_bytes[0]
    address = split_bytes[1]

    #Split the Packet Type
    has_data = (((packet_type & 0b10000000) >> 7) == 1)
    is_batch = (((packet_type & 0b01000000) >> 6) == 1)
    batch_length = (packet_type & 0b00111100) >> 2
    hidden = (((packet_type & 0b00000010) >> 1) == 1)
    command_failed = ((packet_type & 0b00000001) == 1)

    #Determine data length
    #4 times the batch length, or 4 bytes
    data_len = 4*batch_length if is_batch else 4

    return data_len


if __name__ == '__main__':
    main()