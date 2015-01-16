from __future__ import print_function
import serial
import struct
import GP9_packet

class GP9_data(object):
    """Reads data from a CHRobotics GP9
    Has ability to read continuously or one packet at a time
    """
    def __init__(self, serial_port = '/dev/ttyO2', baudrate = 115200):
        super(GP9_data, self).__init__()
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.packets = []
        self.port_open = False

    def open_port(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=10)
            if self.ser.isOpen():
                self.port_open = True
            return self.port_open
        except serial.SerialException:
            return False

    def close_port(self):
        self.ser.close()
        if !self.ser.isOpen():
            self.port_open = False

        # Return true on successful closing
        return !self.port_open

    def read_one_packet(self):
        byte_hist = [0,0,0]
        while byte_hist != ['p', 'n', 's']:
                # find start of packet
                read_byte = self.ser.read(1)
                byte_hist.pop()
                byte_hist.insert(0, read_byte)

        # Have start of packet, read it in
        header_bytes = self.ser.read(2)
        this_packet = GP9_packet.GP9_packet(header=header_bytes)

        data = self.ser.read(this_packet.data_length)
        this_packet.set_data(data)
        checksum = self.ser.read(2)
        this_packet.set_checksum(checksum)

        return this_packet


    def read_loop(self):
        try:
            while True:
                packet = self.read_one_packet()
                if packet.address = 120:
                    packet_data = GP9_packet.DataDecoder.decode(packet)
                    #self.packets.append(packet_data)
                    print(packet_data.data)
        except (KeyboardInterrupt, SystemExit):
            self.ser.close()
            print('Closed serial port.')


def main():
    data_reader = GP9_data()
    if data_reader.open_port():
        data_reader.read_one_packet()
    else:
        print('Could not open serial port')
    

if __name__ == '__main__':
    main()
