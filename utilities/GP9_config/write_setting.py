import GP9SerialInterface
import GP9Config
import GP9Reader
import sys

def main(argv):
    """This script writes to a register the data specified on the command line

    To run the program from the command line, pass:
    write_setting.py [Address] [Parameter1] [Parameter2] []

    Damian Manda 02/06/14
    """
    if len(argv) > 1:
        address = int(argv[0])
        parameters = argv[1:]
        interface = GP9SerialInterface.GP9SerialInterface('/dev/ttyO2')
        
        data_enc = GP9DataFormat.data_encoder(address)
        if data_enc is not None:
            data_enc(data_values=parameters)
            write_packet = GP9Config.PacketConstructor(data=data_enc)
            # Actually transmit the packet, and check for ack
            if interface.send_packet(write_packet):
                interface.close_port()
                response = interface.read_specific_packet(address)
                decoded_resp = GP9Reader.DataDecoder.decode(response)
                if decoded_resp is not None:
                    decoded_resp.print_data() 
        else:
            print('Invalid Register Address')


if __name__ == '__main__':
    # Remove the filename argument
    main(sys.argv[1:])
