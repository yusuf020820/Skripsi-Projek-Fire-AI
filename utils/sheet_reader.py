# utils/sheet_reader.py
import pandas as pd, re
from datetime import datetime
from typing import Literal, Optional

class SheetReader:
    def __init__(self, csv_path="models/dataset.csv"):
        self.csv_path = csv_path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        return self._normalize(df)

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {"Tanggal":"tanggal","Pukul":"pukul","Kawasan":"kawasan","Obyek":"obyek"}
        df = df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})
        # parse tanggal (day-first)
        tgl = pd.to_datetime(df.get("tanggal"), dayfirst=True, errors="coerce")
        # parse pukul (ambil jam pertama)
        def pjam(x: Optional[str]):
            if pd.isna(x): return None
            m = re.search(r"(\d{1,2})[:\.](\d{2})", str(x))
            return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None
        jam = df.get("pukul").apply(pjam) if "pukul" in df.columns else None
        wkt = pd.to_datetime(jam, format="%H:%M", errors="coerce")
        dt = tgl.fillna(method="ffill")  # fallback sederhana
        dt = pd.to_datetime(dt.dt.strftime("%Y-%m-%d") + " " + wkt.dt.strftime("%H:%M").fillna("00:00"),
                            errors="coerce")
        df["dt"] = dt
        df["year"] = df["dt"].dt.year
        df["month"] = df["dt"].dt.strftime("%Y-%m")
        df["day"] = df["dt"].dt.date
        return df

    def aggregate(self, by: Literal["day","month","year"]="month",
                  kawasan: Optional[str]=None, obyek: Optional[str]=None):
        df = self.load()
        if kawasan and "kawasan" in df.columns:
            df = df[df["kawasan"].astype(str).str.lower()==kawasan.lower()]
        if obyek and "obyek" in df.columns:
            df = df[df["obyek"].astype(str).str.lower()==obyek.lower()]

        if by=="day":  idx, series = "day", df.groupby("day").size()
        elif by=="year": idx, series = "year", df.groupby("year").size()
        else:           idx, series = "month", df.groupby("month").size()
        out = series.reset_index()
        out.columns = ["label","count"]
        out = out.sort_values("label")
        return out
