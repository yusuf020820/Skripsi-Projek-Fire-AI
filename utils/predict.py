# utils/predict.py
import joblib
import numpy as np
import os

# === Load model dummy ===
MODEL_PATH = os.path.join("model", "trained_model_dummy.pkl")

try:
    model_data = joblib.load(MODEL_PATH)
except FileNotFoundError:
    raise Exception(f" Model tidak ditemukan di: {MODEL_PATH}")

model_air = model_data['model_air']
model_mobil = model_data['model_mobil']
encoder = model_data['encoder']
features = model_data['features']

def predict_kebutuhan(lokasi, kawasan, obyek, jam, bulan):
    """
    Melakukan prediksi kebutuhan air dan mobil berdasarkan input pengguna.
    """
    if not all([lokasi, kawasan, obyek]) or jam is None or bulan is None:
        return "❌ Input tidak lengkap.", None

    try:
        # Urutkan input sesuai urutan fitur saat training
        input_data = [[lokasi, kawasan, obyek, jam, bulan]]
        encoded_input = encoder.transform(input_data)

        # Prediksi
        air_pred = model_air.predict(encoded_input)[0]
        mobil_pred = model_mobil.predict(encoded_input)[0]

        # Bulatkan hasil
        return round(air_pred, 2), int(round(mobil_pred))

    except Exception as e:
        return f"❌ Terjadi kesalahan saat prediksi: {str(e)}", None

# === Contoh penggunaan langsung ===

from recorder import simpan_ke_google_sheet

# Contoh pengiriman
simpan_ke_google_sheet(
    nama="Komarudin",
    lokasi="Jl. Reungas, Gempolsari, Bandung",
    obyek="Alang-Alang/Lahan Kosong",
    air=12.5,
    mobil=2
)
