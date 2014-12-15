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
                return True
            else:
                return False
        except serial.SerialException:
            return False

    def read_one_packet(self):
        byte_hist = [0,0,0]
        while byte_hist != ['p', 'n', 's']:
                # find start of packet
                read_byte = self.ser.read(1)
                # read_up = struct.unpack('<B', read_byte)
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
                self.packets.append(self.read_one_packet())
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self.ser.close()


def main():
    data_reader = GP9_data()
    if data_reader.open_port():
        data_reader.read_one_packet()
    else:
        print('Could not open serial port')
    

if __name__ == '__main__':
    main()
