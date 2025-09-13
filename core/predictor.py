# core/predictor.py

import joblib
import numpy as np
import pandas as pd

class FirePredictor:
    def __init__(self, model_path: str):
        
      
        self.model_bundle = joblib.load(model_path)
        self.model_air = self.model_bundle['model_air']
        self.model_mobil = self.model_bundle['model_mobil']
        self.encoder = self.model_bundle['encoder']
        self.features = self.model_bundle['features']

    def predict(self, input_dict: dict) -> dict:
       
        try:
            
            input_df = pd.DataFrame([input_dict], columns=self.features)
            encoded = self.encoder.transform(input_df)

           
            pred_air = round(float(self.model_air.predict(encoded)[0]), 2)
            pred_mobil = round(float(self.model_mobil.predict(encoded)[0]))

            return {
                "air": pred_air,
                "mobil": pred_mobil
            }

        except Exception as e:
            return {
                "error": f"Gagal prediksi: {str(e)}"
            }
