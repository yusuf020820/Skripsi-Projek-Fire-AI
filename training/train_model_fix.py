# training/train_real_model.py
import pandas as pd
import joblib, json, os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

# === Load Data Real ===
df = pd.read_csv("data/data.csv")
features = ['lokasi', 'kawasan', 'obyek_standar']
target_air = 'air (m3)'
target_mobil = 'jumlah_mobil_air'

# === Preprocessing ===
df_clean = df[features + [target_air, target_mobil]].dropna()
encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
X = encoder.fit_transform(df_clean[features])
y_air = df_clean[target_air].values
y_mobil = df_clean[target_mobil].values

# === Split Data 80:20 ===
X_train, X_test, y_air_train, y_air_test, y_mobil_train, y_mobil_test = train_test_split(
    X, y_air, y_mobil, test_size=0.2, random_state=42
)

# === Train Models ===
model_air = RandomForestRegressor(n_estimators=100, random_state=42)
model_air.fit(X_train, y_air_train)

model_mobil = RandomForestRegressor(n_estimators=100, random_state=42)
model_mobil.fit(X_train, y_mobil_train)

# === Evaluation ===
y_air_pred = model_air.predict(X_test)
y_mobil_pred = model_mobil.predict(X_test)
evaluation = {

    "MAE_air": round(mean_absolute_error(y_air_test, y_air_pred), 2),
    "MSE_air": round(mean_squared_error(y_air_test, y_air_pred), 2),
    "R2_air": round(r2_score(y_air_test, y_air_pred), 2),

    "MAE_mobil": round(mean_absolute_error(y_mobil_test, y_mobil_pred), 2),
    "MSE_mobil": round(mean_squared_error(y_mobil_test, y_mobil_pred), 2),
    "R2_mobil": round(r2_score(y_mobil_test, y_mobil_pred), 2)
}

# === Save Model & Eval ===
os.makedirs("model", exist_ok=True)
joblib.dump({
    'model_air': model_air,
    'model_mobil': model_mobil,
    'encoder': encoder,
    'features': features
}, "model/trained_model_real.pkl")

Path("model/evaluation_real.json").write_text(json.dumps(evaluation, indent=2))
print("✅ Model real selesai dilatih dan disimpan.")
print(json.dumps(evaluation, indent=2))
