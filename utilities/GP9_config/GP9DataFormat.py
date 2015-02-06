import struct

class DataFormat(object):
    """Defines the super class for data formats"""
    def __init__(self, raw_data=None, data_values=None, has_data=True,
                 is_batch=False, batch_len=0):
        self.data = None
        self.raw_data = raw_data
        # Make a copy of these data lists
        if data_values is None:
            self.data_values = data_values
            self.data_values = data_values
        else:
            self.data_values = [x for x in data_values]
            self.encode_values = [x for x in data_values]

        self.has_data = has_data
        self.is_batch = is_batch
        self.batch_len = batch_len
        # Do the decoding or encoding if something was passed in
        if self.raw_data != None:
            self.decode()
        elif data_values != None:
            self.encode()

    def encode(self):
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
            for field in self.data:
                 print('{0}: {1:.2f}'.format(field, self.data[field]))
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
        super(Data120, self).__init__(raw_data, data_values, True, True, 3)

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
class Data0(DataFormat):
    """Handles the CREG_COM_SETTINGS data register

    Input Tuple:
    Baud Rate: 0-11
    0
    GPS: 0/1
    Sat Info: 0/1
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('baud rate', 'none', 'GPS', 'Sat Info')
        self.field_formats = ('B', 'B', 'B', 'B')
        self.address = 86
        super(Data0, self).__init__(raw_data, data_values, True, False, 0)

    def decode(self):
        raise NotImplementedError()

    def encode(self):
        if len(self.data_values) != len(self.field_names):
            raise Exception('Incorrect number of data values')
        # Note that this cannot be run multiple times, perhaps test for this?
        self.encode_values[0] = self.encode_values[0] << 4
        self.encode_values[3] = self.encode_values[3] << 4
        super(Data0, self).encode()

class DataXX(DataFormat):
    """Handles the XX data register
    """
    def __init__(self, raw_data=None, data_values=None):
        self.field_names = ('baud rate', 'none')
        self.field_formats = ('H', 'H')
        self.address = 86
        super(DataXX, self).__init__(raw_data, data_values)

    def decode(self):
        raise NotImplementedError()

    def encode(self):
        # This is raw data, no need to write
        raise NotImplementedError()
