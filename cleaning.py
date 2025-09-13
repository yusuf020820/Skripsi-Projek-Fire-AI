# scripts/make_dataset_6000.py
import re, os
import numpy as np
import pandas as pd
from pathlib import Path

SRC = "data/data3.csv"
OUT = "data/data_augmented_6000.csv"
TARGET_SIZE = 6000

def extract_kecamatan(lokasi: str) -> str:
    if not isinstance(lokasi, str): return "lainnya"
    m = re.search(r"(?i)kecamatan\s+([a-zA-Z\s]+)", lokasi)
    kec = m.group(1).strip() if m else ""
    return kec.title() if kec else "Lainnya"

# Standarisasi obyek ke kategori kecil yang konsisten
def std_obyek(obyek: str) -> str:
    s = (obyek or "").lower()
    if any(k in s for k in ["rumah", "kontrakan", "kos", "asrama"]): return "rumah"
    if any(k in s for k in ["toko", "ruko", "counter", "kios", "cafe", "kafe", "warung", "resto", "kedai"]): return "toko"
    if any(k in s for k in ["pasar"]): return "pasar"
    if any(k in s for k in ["pabrik", "industri", "gudang"]): return "pabrik"
    if any(k in s for k in ["panel listrik", "gardu", "trafo", "kabel listrik", "listrik"]): return "instalasi_listrik"
    if any(k in s for k in ["kantor", "instansi", "sekolah", "kampus"]): return "kantor"
    return "lainnya"

def jam_bucket(jam):
    try:
        h = int(jam)
    except:
        return "siang"
    if   0 <= h <= 5:   return "dini"
    elif 6 <= h <= 11:  return "pagi"
    elif 12 <= h <= 17: return "siang"
    else:               return "malam"

def main():
    assert os.path.exists(SRC), f"File tidak ditemukan: {SRC}"
    df = pd.read_csv(SRC)

    # pastikan kolom yang dipakai ada
    needed = ["lokasi","kawasan","obyek","air","mobil","jam","bulan"]
    miss = [c for c in needed if c not in df.columns]
    if miss:
        raise ValueError(f"Kolom hilang di data real: {miss}")

    # bersihkan/standar
    df["kecamatan"]   = df["lokasi"].apply(extract_kecamatan)
    df["obyek_std"]   = df["obyek"].apply(std_obyek)
    df["kawasan_std"] = df["kawasan"].astype(str).str.strip().str.lower()
    df["bulan"]       = pd.to_numeric(df["bulan"], errors="coerce").fillna(1).astype(int).clip(1,12)
    df["jam"]         = pd.to_numeric(df["jam"], errors="coerce").fillna(12).astype(int).clip(0,23)
    df["jam_bucket"]  = df["jam"].apply(jam_bucket)

    # target bersih
    df["air"]   = pd.to_numeric(df["air"], errors="coerce")
    df["mobil"] = pd.to_numeric(df["mobil"], errors="coerce").round().astype("Int64")
    df = df.dropna(subset=["air","mobil"]).copy()

    # clip outlier ekstrem supaya model tidak ketarik habis
    cap = df["air"].quantile(0.99)
    df["air"] = df["air"].clip(upper=cap)

    base_cols = ["kecamatan","kawasan_std","obyek_std","bulan","jam","jam_bucket","air","mobil"]

    # kalau data sudah >= TARGET_SIZE, cukup sampling ulang agar pas 6000
    if len(df) >= TARGET_SIZE:
        final = df.sample(TARGET_SIZE, replace=False, random_state=42)[base_cols].reset_index(drop=True)
        final.to_csv(OUT, index=False)
        print(f"✅ Disimpan: {OUT} (ambil sampel dari real), rows={len(final)}")
        return

    # ------- generate dummy -------
    n_need = TARGET_SIZE - len(df)
    rng = np.random.default_rng(42)

    # Distribusi kategorikal dari data real
    p_kec   = df["kecamatan"].value_counts(normalize=True)
    p_kaw   = df["kawasan_std"].value_counts(normalize=True)
    p_obj   = df["obyek_std"].value_counts(normalize=True)
    p_jb    = df["jam_bucket"].value_counts(normalize=True)

    # Untuk nilai numerik, sampling dari real + noise ringan
    air_mean, air_std = df["air"].mean(), max(df["air"].std(), 1.0)
    mob_counts = df["mobil"].value_counts(normalize=True)

    def sample_cat(series_prob):
        cats = series_prob.index.to_list()
        probs= series_prob.values
        return rng.choice(cats, p=probs)

    dummies = []
    for _ in range(n_need):
        kec  = sample_cat(p_kec)
        kaw  = sample_cat(p_kaw)
        obj  = sample_cat(p_obj)
        jb   = sample_cat(p_jb)
        # jam dari bucket
        if jb == "dini":  jam = int(rng.integers(0,6))
        elif jb == "pagi": jam = int(rng.integers(6,12))
        elif jb == "siang":jam = int(rng.integers(12,18))
        else:              jam = int(rng.integers(18,24))
        bulan = int(rng.integers(1,13))

        # air ~ normal di sekitar mean, lalu sesuaikan sedikit berdasar obyek/kawasan
        air = rng.normal(air_mean, air_std*0.9)
        if obj in ["pabrik","pasar"]: air *= 1.2
        if obj in ["rumah","toko"]:   air *= 0.9
        if kaw in ["pemukiman"]:       air *= 0.95
        air = float(np.clip(air, 2.0, cap))  # batas bawah 2 m3

        # mobil: sampling dari distribusi nyata + penyesuaian ringan
        mob = int(rng.choice(mob_counts.index.to_list(), p=mob_counts.values))
        if obj in ["pabrik","pasar"]: mob = max(mob, 3)
        if obj in ["rumah","toko"]:   mob = max(mob, 1)

        dummies.append({
            "kecamatan":kec, "kawasan_std":kaw, "obyek_std":obj,
            "bulan":bulan, "jam":jam, "jam_bucket":jb,
            "air":round(air,2), "mobil":mob
        })

    df_dummy = pd.DataFrame(dummies)
    final = pd.concat([df[base_cols], df_dummy[base_cols]], ignore_index=True)
    final.to_csv(OUT, index=False)
    print(f"✅ Disimpan: {OUT} (real+dummy), rows={len(final)}")

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    main()
