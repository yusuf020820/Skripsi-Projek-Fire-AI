
import joblib, pandas as pd
from typing import Any, Dict

def _canon(s: Any):
    return s.strip().lower() if isinstance(s, str) else s

class FirePredictor:
    def __init__(self, model_path: str):
        b = joblib.load(model_path)
        self.pipe_air = b["pipe_air"]
        self.pipe_mobil = b["pipe_mobil"]
        self.features = b.get("features", ["kawasan","obyek","bulan","jam"])

    def predict(self, inp: Dict[str, Any]) -> Dict[str, Any]:
        try:
            x = {k: _canon(v) for k, v in inp.items()}
          
            try: x["bulan"] = int(x.get("bulan", 1))
            except: x["bulan"] = 1
            try: x["jam"] = int(x.get("jam", 12))
            except: x["jam"] = 12

            row = {k: x.get(k) for k in self.features}
            df = pd.DataFrame([row], columns=self.features)

            air = float(self.pipe_air.predict(df)[0])
            mobil = int(self.pipe_mobil.predict(df)[0])  
            return {"air": round(air, 2), "mobil": mobil}
        except Exception as e:
            return {"error": f"Gagal prediksi: {e}"}
