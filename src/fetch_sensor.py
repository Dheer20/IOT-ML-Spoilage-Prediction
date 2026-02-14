import serial
import time

def open_serial(COM):

    ser = serial.Serial(
        port=COM,
        baudrate=115200,
        timeout=1,
        )
            
    time.sleep(2)
    ser.reset_input_buffer()
    return ser

def get_sensor_data(ser):
    if ser.in_waiting:
        line = ser.readline().decode(errors='ignore').strip()

        if line:
            match line:
                case "b":
                    print("BH sensor not detected")                 
                case "f":
                    print("Sensors giving NaN value")
                    
            # print(repr(line))
            try:
                hum, tem, lux = map(float, line.split(','))
                # print(hum, tem, lux)
                return {
                    "temperature":tem,
                    "humidity":hum,
                    "light":lux
                }
            except ValueError:
                return 0
    
