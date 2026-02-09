from src.io_utils import load_pickle
from src.preprocess import preprocess_data
import pandas as pd
import numpy as np

class_encoder = load_pickle("class_encoder.pkl")
fruit_encoder = load_pickle("fruit_encoder.pkl")
model = load_pickle("spoilage_model.pkl")
scaler = load_pickle("scaler.pkl")

def predict_spoilage (sensor_data,fruit):

    """
    sensor_data: dict with keys -> temperature, humidity, light
    
    fruit: string (e.g. 'Banana')
    """

    X_scaled = preprocess_data(sensor_data,fruit,scaler,fruit_encoder)

    # predicting the probabilities
    probs = model.predict_proba(X_scaled)[0]

    # processing the predicted_class i.e. good or bad
    class_index = np.argmax(probs)
    predicted_class = class_encoder.inverse_transform([class_index])[0]

    # getting the index,probability for bad and good
    bad_index = class_encoder.transform(["Bad"])[0]
    good_index = class_encoder.transform(["Good"])[0]

    p_bad = probs[bad_index]
    p_good = probs[good_index]

    if p_bad < 0.2:
        status = "Fresh"
    elif p_bad < 0.5:
        status = "Monitor"
    elif p_bad < 0.75:
        status = "Warning"
    else:
        status = "Urgent"

    # calculating spoilage risk by using probabilty of bad
    spoilage_risk = int(p_bad * 100)

    confidence = int(abs(p_good - p_bad) * 100)

    if p_bad < 0.2:
        shelf_life = "~48 hours"
    elif p_bad < 0.5:
        shelf_life = "~24 hours"
    elif p_bad < 0.75:
        shelf_life = "~12 hours"
    else:
        shelf_life = "<6 hours"
 
    return {
        "class":predicted_class,
        "status": status,
        "spoilage_risk":spoilage_risk,
        "confidence":confidence,
        "shelf_life":shelf_life
    }



