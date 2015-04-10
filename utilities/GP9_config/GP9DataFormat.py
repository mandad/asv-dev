import struct
import pdb

def data_encoder(address, data_values):
    data = None
    class_names = {0: Config0, 1: Config1, 2: Config2, 3: Config3, 4: Config4, \
        5: Config5, 6: Config6, 7: Config7, 8: Config8, 9: Config9, 10: Config10, \
        11: Config11}
    if address in class_names.keys():
        data = class_names[address]
    return data


class CommandResponse(object):
    def __init__(self, address, successful):
        self.address = address
        #For compatibility with DataFormat usage
        self.data = None
        self.has_data = False
        if successful:
            self.successful = 'success'
        else:
            self.successful = 'failure'

    def print_data(self):
        print('Command Response: address {0}, result {1}'.format(self.address, \
            self.successful))


class DataFormat(object):
    """Defines the super class for data formats"""
    def __init__(self, raw_data=None, data_values=None,
                 is_batch=False, batch_len=0):
        self.data = None
        self.raw_data = raw_data
        # Make a copy of these data lists
        if data_values is None:
            self.data_values = data_values
            self.encode_values = data_values
        else:
            self.data_values = [x for x in data_values]
            self.encode_values = [x for x in data_values]

        self.has_data = True
        self.is_batch = is_batch
        self.batch_len = batch_len
        # Do the decoding or encoding if something was passed in
        if self.raw_data != None:
            self.decode()
        elif data_values != None:
            self.encode()

    def encode(self):
        if len(self.data_values) != len(self.field_names):
            raise Exception('Incorrect number of data values')
        self.raw_data = ''
        for item in zip(self.field_formats, self.encode_values):
            self.raw_data = self.raw_data + struct.pack('>' + item[0], item[1])
        # Note that the data values may be different from those encoded
        self.data = dict(zip(self.field_names, self.data_values))

    def decode(self):
        concat_format = '>'
        for bit_format in self.field_formats:
            concat_format = concat_format + bit_format
        try:
            decoded_data = list(struct.unpack(concat_format, self.raw_data))
            self.data = dict(zip(self.field_names, decoded_data))
        except Exception, e:
            print('Could not parse data: %s' % str(e))

    def print_data(self):
        if self.data != None:
            # Note that this is not the same as all the self.field_names because
            # blank fields may have been removed
            pdb.set_trace()
            for field in self.data:
                 print('{0s}: {1:.2f}'.format(field, self.data[field]))
        else:
            print('No Decoded Data')

    @staticmethod
    def twos_complement(val, bits):
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

class Data120(DataFormat):
    """Handles the Euler Angle packet, which is a batch of 3
    Variables:
    data - Contains a dictionary with the data descriptions and values
    """
    def __init__(self, raw_data=None, data_values=None):
        """raw_data is data to decode
        data_values is data to encode
        """
        # 4th field is unused
        self.field_names = ('roll', 'pitch', 'yaw', 'none', 'time')
        self.field_formats = ('h', 'h', 'h', 'h', 'f')
        self.address = 120
        super(Data120, self).__init__(raw_data, data_values, True, 3)

    def decode(self):
        # Decode into basic numbers
        super(Data120, self).decode()
        #decoded_data.pop(3)
        # Convert the angles to degrees
        for field in self.field_names[0:3]:
            self.data[field] = self.convert_to_rad(self.data[field])

        # Remove unused field
        self.data.pop('none')

    def encode(self):
        for i in range(3):
            self.encode_values[i] = self.convert_from_rad(self.encode_values[i])
        super(Data120, self).encode()
        self.data.pop('none')

    @staticmethod
    def convert_to_rad(angle_value):
        return angle_value / 5215.18917

    @staticmethod
    def convert_from_rad(angle_value):
        return angle_value * 5215.18917


class Data86(DataFormat):
    """Handles the raw gyro data packet
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('gyro x', 'gyro y', 'gyro z', 'none', 'time')
        self.field_formats = ('H', 'H', 'H', 'H' 'f')
        self.address = 86
        super(Data86, self).__init__(raw_data, data_values)

    def decode(self):
        super(Data86, self).decode()
        # Convert the two's complement numbers
        for field in self.field_names[0:3]:
            self.data[field] = self.twos_complement(self.data[field], 16)

        self.data.pop('none')

    def encode(self):
        # This is raw data, no need to write
        raise NotImplementedError()

#===============================================================================
# Configuration Registers
#===============================================================================
class Config0(DataFormat):
    """Handles the CREG_COM_SETTINGS data register

    Input Tuple
    -----------
    Baud Rate: 0-11
    0
    GPS: 0/1
    Sat Info: 0/1
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('baud rate', 'none', 'GPS', 'Sat Info')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 86
        super(Config0, self).__init__(raw_data, data_values, False, 0)

    def decode(self):
        raise NotImplementedError()

    def encode(self):
        # Note that this cannot be run multiple times, perhaps test for this?
        self.encode_values[0] = self.encode_values[0] << 4
        self.encode_values[3] = self.encode_values[3] << 4
        super(Config0, self).encode()

class Config1(DataFormat):
    """Handles the CREG_COM_RATES1 data register

    Input Tuple
    -----------
    Raw Accel Rate: 0-255
    Raw Gyro Rate: 0-255
    Raw Magnetometer Rate: 0-255
    Raw Pressure Rate: 0-255
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('accel rate', 'gyro rate', 'mag rate', 'press rate')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 1
        super(Config1, self).__init__(raw_data, data_values, False, 0)


class Config2(DataFormat):
    """Handles the CREG_COM_RATES2 data register

    Input Tuple
    -----------
    Raw Temp Rate: 0-255
    0
    0
    All Raw Rate: 0-255
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('temp rate', 'none', 'none2', 'all raw rate')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 2
        super(Config2, self).__init__(raw_data, data_values, False, 0)


class Config3(DataFormat):
    """Handles the CREG_COM_RATES3 data register

    Input Tuple
    -----------
    Processed Acceleration Rate: 0-255
    Proc Gyro Rate: 0-255
    Proc Mag Rate: 0-255
    Proc Pressure Rate: 0-255
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('proc accel rate', 'proc gyro rate', 'proc mag rate', \
            'proc press rate')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 3
        super(Config3, self).__init__(raw_data, data_values, False, 0)


class Config4(DataFormat):
    """Handles the CREG_COM_RATES4 data register

    Input Tuple
    -----------
    Processed Temperature Rate: 0-255
    0
    0
    All Proc Rate: 0-255
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('proc temp rate', 'none', 'none2', 'all proc rate')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 4
        super(Config4, self).__init__(raw_data, data_values, False, 0)


class Config5(DataFormat):
    """Handles the CREG_COM_RATES5 data register

    Input Tuple
    -----------
    Quaternion Rate: 0-255
    Euler Angle Rate: 0-255
    Position Rate: 0-255
    Velocity Rate: 0-255
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('quat rate', 'euler rate', 'posn rate', 'vel rate')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 5
        super(Config5, self).__init__(raw_data, data_values, False, 0)


class Config6(DataFormat):
    """Handles the CREG_COM_RATES6 data register

    Input Tuple
    -----------
    Pose Rate: 0-255
    Health Rate: 0-6
    0
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('pose rate', 'health rate', 'none')
        self.field_formats = ('B', 'B', 'H')
        self.address = 6
        super(Config6, self).__init__(raw_data, data_values, False, 0)

class Config7(DataFormat):
    """Handles the CREG_COM_RATES7 data register.  This provides NMEA style
    output in plain text format.

    Input Tuple
    -----------
    Health Rate: 0-7
    Pose Rate: 0-7
    Attitude Rate: 0-7
    Sensor Rate: 0-7
    0
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('health/pose rate', 'attitude/sensor rate', 'none')
        self.field_formats = ('B', 'B', 'H')
        self.address = 7
        super(Config7, self).__init__(raw_data, data_values, False, 0)

    def decode(self):
        raise NotImplementedError()

    def encode(self):
        self.encode_values[0] = (self.data_values[0] << 4) + self.data_values[1]
        self.encode_values[1] = (self.data_values[2] << 4) + self.data_values[3]
        # Remove the two extra values
        self.encode_values.pop(2)
        self.encode_values.pop(2)
        super(Config7, self).encode()

class Config8(DataFormat):
    """Handles the CREG_FILTER_SETTINGS data register.

    Input Tuple
    -----------
    Use GPS: 0/1
    Use Magnetomter: 0/1
    Use Accelerometers: 0/1
    0
    0
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('GPS/Mag/Accel', 'none', 'none2')
        self.field_formats = ('B', 'B', 'H')
        self.address = 8
        super(Config8, self).__init__(raw_data, data_values, False, 0)

    def decode(self):
        raise NotImplementedError()

    def encode(self):
        self.encode_values[0] = (self.data_values[0] << 6) \
            + (self.data_values[1] << 5) + (self.data_values[2] << 4)
        self.encode_values.pop(1)
        self.encode_values.pop(1)
        super(Config8, self).encode()

class Config9(DataFormat):
    """Handles the CREG_HOME_NORTH data register.

    Input Tuple
    -----------
    Latitude of Home Position in Decimal Degrees
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('LatHome')
        self.field_formats = ('f')
        self.address = 9
        super(Config9, self).__init__(raw_data, data_values, False, 0)

class Config10(DataFormat):
    """Handles the CREG_HOME_EAST data register.

    Input Tuple
    -----------
    Longitude of Home Position in Decimal Degrees
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('LonHome')
        self.field_formats = ('f')
        self.address = 10
        super(Config10, self).__init__(raw_data, data_values, False, 0)

class Config11(DataFormat):
    """Handles the CREG_HOME_UP data register.

    Input Tuple
    -----------
    Elevation of Home Position in meters
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('ElevHome')
        self.field_formats = ('f')
        self.address = 11
        super(Config11, self).__init__(raw_data, data_values, False, 0)

class DataXX(DataFormat):
    """Handles the XX data register
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('baud rate', 'none')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = XX
        super(DataXX, self).__init__(raw_data, data_values, False, 0)

    def decode(self):
        raise NotImplementedError()

    def encode(self):
        raise NotImplementedError()
