
import os
import re
from typing import Optional, List, Literal

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials


STANDARD_COLUMNS = [
    "Waktu", "Waktu_dt", "Nama Pelapor", "Alamat",
    "Kecamatan", "Kawasan",
    "Obyek", "Air", "Mobil",
    "Tanggal", "Pukul", "Bulan"
]


KECAMATAN_BANDUNG: List[str] = [
    "Andir","Antapani","Arcamanik","Astanaanyar","Babakan Ciparay","Bandung Kidul",
    "Bandung Kulon","Bandung Wetan","Batununggal","Bojongloa Kaler","Bojongloa Kidul",
    "Buahbatu","Cibeunying Kaler","Cibeunying Kidul","Cibiru","Cicendo","Cidadap",
    "Cinambo","Coblong","Gedebage","Kiaracondong","Lengkong","Mandalajati",
    "Panyileukan","Rancasari","Regol","Sukajadi","Sukasari","Sumur Bandung","Ujungberung"
]

def _extract_hhmm(text: Optional[str]) -> Optional[str]:
  
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    m = re.search(r"(\d{1,2})[:\.](\d{2})", str(text)) 
    if not m:
        return None
    hh, mm = int(m.group(1)), m.group(2)
    return f"{hh:02d}:{mm}"

def _parse_ambiguous_datetime(s: Optional[str]) -> pd.Timestamp:
  
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return pd.NaT
    s = str(s).strip()
    if not s:
        return pd.NaT

   
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm, ss = int(m.group(4) or 0), int(m.group(5) or 0), int(m.group(6) or 0)
        try:
            return pd.Timestamp(y, mo, d, hh, mm, ss)
        except ValueError:
            return pd.to_datetime(s, errors="coerce")

   
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm, ss = int(m.group(4) or 0), int(m.group(5) or 0), int(m.group(6) or 0)
        prefer_dmy = True 

       
        if b > 12 and a <= 12:
            mo, d = a, b
       
        elif a > 12 and b <= 12:
            d, mo = a, b
        else:
           
            if prefer_dmy:
                d, mo = a, b   
                mo, d = a, b   

        try:
            return pd.Timestamp(y, mo, d, hh, mm, ss)
        except ValueError:
          
            return pd.to_datetime(f"{y}-{mo:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}", errors="coerce")

   
    return pd.to_datetime(s, dayfirst=True, errors="coerce")

def _guess_kecamatan_from_alamat(alamat: Optional[str]) -> str:
  
    if not isinstance(alamat, str) or not alamat.strip():
        return "Lainnya"
    low = alamat.lower()
    for kec in KECAMATAN_BANDUNG:
        if kec.lower() in low:
            return kec
    parts = [p.strip() for p in alamat.split(",") if p.strip()]
    return parts[-1] if parts else "Lainnya"

class SheetReader:
    def __init__(self, sheet_name: Optional[str] = None,
                 cred_filename: Optional[str] = None,
                 worksheet: Optional[str] = None):
        self.sheet_name = sheet_name or os.getenv("GSHEET_NAME", "PrediksiKebakaran")
        cred_filename = cred_filename or os.getenv("GSHEET_CRED_FILE", "gsheet-cred.json") #ganti gsheet-cred.json dengan nama folder yang ada di secrete
        self.worksheet = worksheet  # 

        base_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.normpath(os.path.join(base_dir, "..", "secrets", cred_filename))

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
        client = gspread.authorize(creds)
        self.sheet = client.open(self.sheet_name).worksheet(self.worksheet) if self.worksheet else client.open(self.sheet_name).sheet1

  
    def get_dataframe(self) -> pd.DataFrame:
        try:
            records = self.sheet.get_all_records()
            df = pd.DataFrame(records)
            if df.empty:
                return self._empty_df()
            df = self._normalize_columns(df)
            df = self._ensure_time_columns(df)
            df = self._ensure_kecamatan_kawasan(df)
            df = self._finalize_columns(df)
            return df
        except Exception as e:
            print(f" Gagal membaca Google Sheet: {e}")
            return self._empty_df()

    def aggregate(self, by: str = "month", kecamatan: str | None = None,
                  alamat_contains: str | None = None, obyek: str | None = None) -> pd.DataFrame:
    
        df = self.get_dataframe()
        if df.empty:
            return pd.DataFrame(columns=["label","count"])

      
        if "Waktu_dt" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Waktu_dt"]):
            dt = df["Waktu_dt"]
        elif "Waktu" in df.columns:
            dt = pd.to_datetime(df["Waktu"], errors="coerce", dayfirst=True)
        else:
            return pd.DataFrame(columns=["label","count"])
        df = df.assign(__dt=dt).dropna(subset=["__dt"])

   
        col_kec = "Kecamatan" if "Kecamatan" in df.columns else ("Kawasan" if "Kawasan" in df.columns else None)
        col_oby = "Obyek" if "Obyek" in df.columns else ("Objek" if "Objek" in df.columns else None)

        
        if kecamatan and col_kec:
            key = str(kecamatan).strip().lower()
            df = df[df[col_kec].astype(str).str.strip().str.lower() == key]

       
        if alamat_contains and "Alamat" in df.columns:
            sub = str(alamat_contains).strip().lower()
            df = df[df["Alamat"].astype(str).str.lower().str.contains(sub, na=False)]

       
        if obyek and col_oby:
            key = str(obyek).strip().lower()
            df = df[df[col_oby].astype(str).str.strip().str.lower() == key]

     
        by = (by or "month").lower()
        if by == "day":
            df["label"] = df["__dt"].dt.strftime("%Y-%m-%d")
        elif by == "year":
            df["label"] = df["__dt"].dt.strftime("%Y")
        else:  
            df["label"] = df["__dt"].dt.strftime("%Y-%m")

        out = df.groupby("label", as_index=False).size().rename(columns={"size": "count"})
        out = out.sort_values("label")
        return out[["label","count"]]
    
   
    def _empty_df(self) -> pd.DataFrame:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rapikan header dan alias, pastikan tipe numerik aman."""
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]

       
        alias_map = {
            "Alamat ": "Alamat",
            "Waktu ": "Waktu",
            "Objek": "Obyek",
            "Object": "Obyek",
            "Nama": "Nama Pelapor",
            "Pelapor": "Nama Pelapor",
            "Nama Pelapor ": "Nama Pelapor",
            "Jam": "Pukul",
        }
        for src, dst in alias_map.items():
            if src in df.columns and dst not in df.columns:
                df.rename(columns={src: dst}, inplace=True)

        
        for col, default in [
            ("Nama Pelapor", None),
            ("Alamat", None),
            ("Obyek", None),
            ("Air", None),
            ("Mobil", None),
            ("Bulan", None),
        ]:
            if col not in df.columns:
                df[col] = default

       
        for num_col in ("Air", "Mobil", "Bulan"):
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

        return df

    def _ensure_time_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Bangun 'Waktu_dt' (datetime) dengan prioritas:
          1) parse langsung dari 'Waktu' (auto DMY/MDY)
          2) gabungan 'Tanggal' + 'Pukul' (ambil HH:MM pertama)
          3) fallback NaT
        Bentuk 'Waktu' string jika belum ada.
        """
        df = df.copy()

        waktu_dt = None
        if "Waktu" in df.columns:
           
            waktu_dt = df["Waktu"].apply(_parse_ambiguous_datetime)

        if waktu_dt is None or getattr(waktu_dt, "isna", lambda: True)().all():
            T = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=True) if "Tanggal" in df.columns else None
            P = df["Pukul"].apply(_extract_hhmm) if "Pukul" in df.columns else None

            if T is not None and (P is not None or not T.isna().all()):
                if P is not None:
                    jam = pd.Series(P).fillna("00:00")
                    waktu_dt = pd.to_datetime(T.dt.strftime("%Y-%m-%d") + " " + jam, errors="coerce")
                else:
                    waktu_dt = T
            else:
                waktu_dt = pd.Series(pd.NaT, index=df.index)

        df["Waktu_dt"] = waktu_dt

       
        if "Waktu" not in df.columns or df["Waktu"].isna().all():
            df["Waktu"] = df["Waktu_dt"].dt.strftime("%Y-%m-%d %H:%M")

        return df

    def _ensure_kecamatan_kawasan(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ekstrak Kecamatan dari Alamat dan sinkronkan ke Kawasan."""
        df = df.copy()
        df["Kecamatan"] = df["Alamat"].apply(_guess_kecamatan_from_alamat)

        if "Kawasan" not in df.columns or df["Kawasan"].isna().all():
            df["Kawasan"] = df["Kecamatan"]
        else:
            mask = df["Kawasan"].isna() | (df["Kawasan"].astype(str).str.strip() == "")
            df.loc[mask, "Kawasan"] = df.loc[mask, "Kecamatan"]

        return df

    def _finalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pastikan semua kolom standar ada dan urut konsisten."""
        df = df.copy()
        for col in STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[STANDARD_COLUMNS]
