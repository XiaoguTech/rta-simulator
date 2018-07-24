import serial
import pynmea2
import time
ser = serial.Serial('/dev/ttyAMA0', 38400)
print(ser.isOpen())
while True:
    line = ser.readline()
    if line.startswith('$GNRMC'):
        rmc = pynmea2.parse(line)
        print('Latitude:{}, Longitude:{}'.format( float(rmc.lat)/100, float(rmc.lon)/100 ) )
#        break
ser.close()
