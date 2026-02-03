import joblib
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR/"models"
DATA_PATH = BASE_DIR/"data"

def load_dataset(filename):
    df = pd.read_csv(DATA_PATH/filename)
    return df

def save_pickle(obj,filename):
    MODEL_DIR.mkdir(exist_ok = True)
    joblib.dump(obj, MODEL_DIR/filename)

def load_pickle(filename):
    return joblib.load(MODEL_DIR/filename) 