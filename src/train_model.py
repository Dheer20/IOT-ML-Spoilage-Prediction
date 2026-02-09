import pandas as pd
from src.preprocess import clean_dataset, add_sensor_noise
from src.io_utils import save_pickle, load_dataset
from sklearn.preprocessing import LabelEncoder,StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score , classification_report


df = load_dataset("Dataset.csv")

df = clean_dataset(df)

fruit_encoder = LabelEncoder()
df["Fruit_encoded"] = fruit_encoder.fit_transform(df["Fruit"])

class_encoder = LabelEncoder()
df["Class_encoded"] = class_encoder.fit_transform(df["Class"])

X = df[["Temp","Humid (%)", "Light (Fux)","Fruit_encoded"]]
Y = df["Class_encoded"]

X_train, X_test, Y_train, Y_test = train_test_split(
    X,
    Y,
    test_size = 0.2,
    random_state = 22
)

X_train = add_sensor_noise(X_train)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier(
    n_estimators = 100,
    random_state = 22
)

model.fit(X_train_scaled,Y_train)

Y_pred = model.predict(X_test_scaled)

print("Accuracy:", accuracy_score(Y_test, Y_pred))
print(classification_report(Y_test,Y_pred))

save_pickle(model,"spoilage_model.pkl")
save_pickle(scaler,"scaler.pkl")
save_pickle(fruit_encoder,"fruit_encoder.pkl")
save_pickle(class_encoder,"class_encoder.pkl")
