import numpy as np
import pandas as pd

def add_sensor_noise(X):

    X = X.copy()

    if "Temp" in X.columns:
        X["Temp"] += np.random.normal(0, 0.5, size= len(X))

    if "Humid (%)" in X.columns:
        X["Humid (%)"] += np.random.normal(0, 2.0, size = len(X))

    if "Light (Fux)" in X.columns:
        X["Light (Fux)"] += np.random.normal(0, 1.0, size = len(X))

    return X

def clean_dataset(dataset):
    # remove rows with missing values
    dataset = dataset.dropna()
    
    # converting column names to lowercase and removing spaces
    dataset.columns = [column.strip() for column in dataset.columns]

    print(dataset.columns)

    # converting class names to lower and removing spaces
    dataset["Class"] = dataset["Class"].str.strip().str.capitalize()

    return dataset

def preprocess_data(sensor_data,fruit,scaler,fruit_encoder):

    fruit_encoded = fruit_encoder.transform([fruit])[0]

    X = pd.DataFrame(
        [[
            sensor_data["temperature"],
            sensor_data["humidity"],
            sensor_data["light"],
            fruit_encoded
        ]],
        columns = ["Temp","Humid (%)","Light (Fux)","Fruit_encoded"]
    )
    # scaling the inputs before giving them as inputs
    return scaler.transform(X)
