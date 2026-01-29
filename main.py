import pandas as pd
from sklearn.preprocessing import LabelEncoder,StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score , classification_report
import joblib

df = pd.read_csv("Dataset.csv")

# Remove rows with missing values
df = df.dropna()

# Strip spaces in column names
df.columns = df.columns.str.strip()


fruit_encoder = LabelEncoder()
df["Fruit_encoded"] = fruit_encoder.fit_transform(df["Fruit"])

df["Class"] = df["Class"].str.strip().str.capitalize()

class_encoder = LabelEncoder()
df["Class_encoded"] = class_encoder.fit_transform(df["Class"])

X = df[["Temp","Humid (%)", "Light (Fux)","Fruit_encoded"]]
Y = df["Class_encoded"]

X_train, X_test, Y_train, Y_test = train_test_split(
    X,
    Y,
    test_size = 0.2,
    random_state = 42
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier(
    n_estimators = 100,
    random_state = 42
)

model.fit(X_train_scaled,Y_train)

Y_pred = model.predict(X_test_scaled)

print("Accuracy:", accuracy_score(Y_test, Y_pred))
print(classification_report(Y_test,Y_pred))

joblib.dump(model, "spoilage_model.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(fruit_encoder, "fruit_encoder.pkl")
joblib.dump(class_encoder, "class_encoder.pkl")