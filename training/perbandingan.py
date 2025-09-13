# training/perbandingan_fair.py
import pandas as pd
import joblib, os, json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

# === Load Dataset ===
DATASET_PATH = "data/data2.csv"
print(f"✅ Load dataset: {DATASET_PATH}")
df = pd.read_csv(DATASET_PATH)

# === Fitur & Target ===
features = ['lokasi', 'kawasan', 'obyek_standar']
target_air = 'air (m3)'
target_mobil = 'jumlah_mobil_air'

df_clean = df[features + [target_air, target_mobil]].dropna()

# === Encoder yang sama dengan model RF awal ===
encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
X = encoder.fit_transform(df_clean[features])
y_air = df_clean[target_air].values
y_mobil = df_clean[target_mobil].values

# === Split Data Sama ===
X_train, X_test, y_air_train, y_air_test, y_mobil_train, y_mobil_test = train_test_split(
    X, y_air, y_mobil, test_size=0.2, random_state=42
)

# Model RF 
rf_air = RandomForestRegressor(n_estimators=100, random_state=42)
rf_air.fit(X_train, y_air_train)

rf_mobil = RandomForestRegressor(n_estimators=100, random_state=42)
rf_mobil.fit(X_train, y_mobil_train)

# === Model GBR ===
gbr_air = GradientBoostingRegressor(random_state=42)
gbr_air.fit(X_train, y_air_train)

gbr_mobil = GradientBoostingRegressor(random_state=42)
gbr_mobil.fit(X_train, y_mobil_train)

# === Evaluasi ===
def evaluate(model_air, model_mobil, name):
    y_air_pred = model_air.predict(X_test)
    y_mobil_pred = model_mobil.predict(X_test)
    return {
        "MAE_air": round(mean_absolute_error(y_air_test, y_air_pred), 3),
        "MSE_air": round(mean_squared_error(y_air_test, y_air_pred), 3),
        "R2_air": round(r2_score(y_air_test, y_air_pred), 3),
        "MAE_mobil": round(mean_absolute_error(y_mobil_test, y_mobil_pred), 3),
        "MSE_mobil": round(mean_squared_error(y_mobil_test, y_mobil_pred), 3),
        "R2_mobil": round(r2_score(y_mobil_test, y_mobil_pred), 3),
    }

rf_eval = evaluate(rf_air, rf_mobil, "Random Forest")
gbr_eval = evaluate(gbr_air, gbr_mobil, "Gradient Boosting")

print("\n=== HASIL PERBANDINGAN FAIR ===")
print("RF  ->", rf_eval)
print("GBR ->", gbr_eval)

# === Simpan Model & Encoder ===
os.makedirs("model", exist_ok=True)
joblib.dump({
    'model_air_rf': rf_air,
    'model_mobil_rf': rf_mobil,
    'model_air_gbr': gbr_air,
    'model_mobil_gbr': gbr_mobil,
    'encoder': encoder,
    'features': features
}, "model/trained_model_compare_fair.pkl")

Path("model/evaluation_compare_fair real.json").write_text(json.dumps({
    "RandomForest": rf_eval,
    "GradientBoosting": gbr_eval
}, indent=2))

print("\n✅ Model perbandingan tersimpan di model/trained_model_compare_fair.pkl")
print("✅ Evaluasi tersimpan di model/evaluation_compare_fair.json")
