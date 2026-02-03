from src.prediction import predict_spoilage 

sensor_data = {
    "temperature":34,
    "humidity":20,
    "light" : 30
}

results = predict_spoilage(sensor_data = sensor_data)

print(results)