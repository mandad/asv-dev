import serial
import struct

ser = serial.Serial('/dev/ttyO2', 115200, timeout=10)

#snp
ser.read(3)
#packet type
pt = ser.read()
pt_up = struct.unpack('<B', pt)[0]
addr = ser.read()
addr_up = struct.unpack('<B', pt)[0]

#bin(pt_up)
