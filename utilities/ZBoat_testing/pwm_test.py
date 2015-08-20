import sys
import serial

class ZBoatTester(object):
    def __init__(self, serial_port='/dev/ttyUSB0', baudrate=115200):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.ser = None

    def open_port(self, timeout=10):
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=timeout)
            if self.ser.isOpen():
                self.port_open = True
            return self.port_open
        except serial.SerialException:
            return False

    def close_port(self):
        # The port will also close when it is deconstructed
        self.set.close()

    def set_autonomy_mode(self):
        self.ser.write('!SetAutonomousControl\r\n')

    def set_manual_mode(self):
        self.ser.write('!SetManualControl\r\n')

    def write_pwm_values(self, left_thrust, right_thrust, rudder):
        # Make sure they are inside the possible ranges
        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
        left_thrust = clamp(left_thrust, 1.0, 2.0)
        right_thrust = clamp(right_thrust, 1.0, 2.0)
        rudder = clamp(rudder, 1.0, 2.0)

        self.ser.write('!pwm, *, %4.3f, %4.3f, %4.3f, *, *\r\n'.format( \
            left_thrust, right_thrust, rudder))


def main(argv):
    if len(argv == 4):
        thisTester = ZBoatTester(argv[3])
    else:
        thisTester = ZBoatTester()
    thisTester.open_port()
    thisTester.set_autonomy_mode()

    if len(argv) == 2:
        # args = thrust, rudder
        thisTester.write_pwm_values(argv[0], argv[0], argv[1])
    elif len(argv) >= 3:
        # args = left_thrust, right_thrust, rudder
        thisTester.write_pwm_values(argv[0], argv[1], argv[2])

    thisTester.set_manual_mode()
    thisTester.close_port()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage: pwm_test.py thrust rudder')
    else:
        main(sys.argv[1:])
