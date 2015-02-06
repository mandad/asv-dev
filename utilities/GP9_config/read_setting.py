import GP9SerialInterface
import GP9Config
import GP9Reader
import sys

def main(argv):
    """
    This script sends a read request to the specified address, then prints the 
    received response to the console

    Damian Manda 02/06/2015
    """
    if len(argv) > 0:
        address = argv[0]
        interface = GP9SerialInterface.GP9SerialInterface('/dev/ttyO2')
        write_packet = GP9Config.PacketConstructor(read=address)
        if write_packet.ready_to_send:
            interface.open_port()
            interface.send_packet(write_packet)

            #Make a fake packet to start while loop, read until we get a response
            read_packet = object()
            read_packet.address = -1
            while read_packet.address != address:
                read_packet = interface.read_one_packet()

            decoded_data = GP9Reader.DataDecoder.decode(read_packet)
            if decoded_data is not None:
                decoded_data.print_data()
        else:
            print('Error making packet')
    else:
        print('Missing Argument')

if __name__ == '__main__':
    main(sys.argv[1:])
