# test/test_predict_and_log.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.predictor import FirePredictor
from core.logger import GoogleSheetLogger
from datetime import datetime


predictor = FirePredictor("model/trained_model_dummy.pkl")  
logger = GoogleSheetLogger(sheet_name="PrediksiKebakaran")


now = datetime.now()

input_data = {
    "lokasi": "Cihampelas",
    "kawasan": "Pemuskiman",
    "obyek": "pasar",
    "jam": str(now.hour),     
    "bulan": str(now.month) 
}


hasil = predictor.predict(input_data)

if "error" in hasil:
    print(" Gagal prediksi:", hasil["error"])
else:
 
    data_laporan = {
        "tanggal": datetime.now().strftime("%Y-%m-%d"),
        "jam": datetime.now().strftime("%H:%M"),
        "nama": "Simulasi Petugas",
        "lokasi": input_data["lokasi"],
        "obyek": input_data["obyek"],
        "air": hasil["air"],
        "mobil": hasil["mobil"]
    }


    berhasil = logger.simpan_laporan(data_laporan)
    if berhasil:
        print(f"✅ Prediksi: {hasil['air']} m³, {hasil['mobil']} mobil. Data berhasil dicatat.")
    else:
        print("Prediksi berhasil, tapi gagal mencatat ke Google Sheet.")
