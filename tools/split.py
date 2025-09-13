import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder

# === Load Data ===
df = pd.read_csv("data/data_4.csv")

features = ["lokasi", "kawasan", "obyek"]
target_air = "air"
target_mobil = "mobil"

df_clean = df[features + [target_air, target_mobil]].dropna().copy()

# Split dulu
train_df, test_df = train_test_split(df_clean, test_size=0.2, random_state=42)

# Ordinal Encoder (fit di TRAIN SAJA)
ord_enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
ord_enc.fit(train_df[features])

X_train_enc = ord_enc.transform(train_df[features])
X_test_enc  = ord_enc.transform(test_df[features])

# Buat DataFrame hasil encoding
train_enc_df = pd.DataFrame(X_train_enc, columns=features, index=train_df.index)
train_enc_df[target_air] = train_df[target_air].values
train_enc_df[target_mobil] = train_df[target_mobil].values

test_enc_df = pd.DataFrame(X_test_enc, columns=features, index=test_df.index)
test_enc_df[target_air] = test_df[target_air].values
test_enc_df[target_mobil] = test_df[target_mobil].values

# Simpan contoh & full
os.makedirs("lampiran", exist_ok=True)
df_clean.head(20).to_csv("lampiran/sample_dataset.csv", index=False)
train_df.head(16).to_csv("lampiran/sample_training.csv", index=False)
test_df.head(4).to_csv("lampiran/sample_testing.csv", index=False)

train_enc_df.head(16).to_csv("lampiran/sample_training_encoded_ordinal.csv", index=False)
test_enc_df.head(4).to_csv("lampiran/sample_testing_encoded_ordinal.csv", index=False)

train_enc_df.to_csv("lampiran/full_training_encoded_ordinal.csv", index=False)
test_enc_df.to_csv("lampiran/full_testing_encoded_ordinal.csv", index=False)

# (Opsional) Simpan mapping kategori → index untuk dokumentasi skripsi
mapping = {col: list(cats.astype(str)) for col, cats in zip(features, ord_enc.categories_)}
pd.Series(mapping).to_json("lampiran/ordinal_categories_mapping.json", force_ascii=False)

print("✅ Selesai: Ordinal encoding & file contoh tersimpan di folder lampiran/")
