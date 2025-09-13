import pandas as pd

def get_laporan_dataframe():
    try:
        df = pd.read_csv("laporan.csv")  
    except Exception:
        df = pd.DataFrame(columns=["tanggal", "jam", "nama", "lokasi", "obyek", "air", "mobil"])
    return df
