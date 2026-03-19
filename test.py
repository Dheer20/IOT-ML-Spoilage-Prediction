from src.prediction import predict_spoilage 
from src.fetch_sensor import *

serial = open_serial("COM4")

while True:

 
    sensor_data = get_sensor_data(serial)
    if sensor_data:
        results = predict_spoilage(sensor_data = sensor_data,fruit="Banana")

        print(results)