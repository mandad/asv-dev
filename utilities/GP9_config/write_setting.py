import GP9SerialInterface
import GP9Config
import GP9Reader
import sys

def main(argv):
    """This script writes to a register the data specified on the command line

    Damian Manda 02/06/14
    """
    if len(argv) > 1:
        address = int(argv[0])
        parameters = argv[1:]
        interface = GP9SerialInterface.GP9SerialInterface('/dev/ttyO2')
        
        write_packet = GP9Config.PacketConstructor(data=)

if __name__ == '__main__':
    # Remove the filename argument
    main(sys.argv[1:])
