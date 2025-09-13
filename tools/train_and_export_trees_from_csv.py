# tools/train_and_export_trees_from_csv.py
import argparse, os, json, shutil, subprocess, warnings, sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.tree import export_text, export_graphviz
from sklearn import tree

warnings.filterwarnings("ignore", category=UserWarning)

DEFAULT_CSV = "data/data3.csv"

def coerce_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def save_tree_text(estimator, features, outpath):
    txt = export_text(estimator, feature_names=features, decimals=3)
    Path(outpath).write_text(txt, encoding="utf-8")
    return outpath

def save_tree_png(estimator, features, outpath_png, max_depth=4):
    plt.figure(figsize=(18, 10))
    tree.plot_tree(
        estimator,
        feature_names=features,
        filled=True,
        rounded=True,
        max_depth=max_depth,
        impurity=False,
    )
    plt.tight_layout()
    plt.savefig(outpath_png, dpi=150)
    plt.close()
    return outpath_png

def save_tree_graphviz(estimator, features, basename_noext, max_depth=None):
    dot_path = f"{basename_noext}.dot"
    png_path = f"{basename_noext}.png"
    export_graphviz(
        estimator,
        out_file=dot_path,
        feature_names=features,
        filled=True,
        rounded=True,
        max_depth=max_depth,
        impurity=False,
    )
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", dot_path, "-o", png_path], check=True)
        return dot_path, png_path
    return dot_path, None

def save_importances(model, features, out_json):
    imp = model.feature_importances_
    order = np.argsort(imp)[::-1]
    payload = [{"feature": features[i], "importance": float(imp[i])} for i in order]
    Path(out_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

def resolve_csv_path(cli_csv: str | None) -> Path:
    """Pakai CLI jika ada; kalau tidak ada, jatuhkan ke default.
    Validasi keberadaan file, dan berikan saran bila tidak ditemukan."""
    path = Path(cli_csv) if cli_csv else Path(DEFAULT_CSV)
    if not path.exists():
        msg = (
            f"⚠️ File CSV tidak ditemukan: {path}\n"
            f"- Jalankan dengan argumen --csv <path_ke_csv>\n"
            f"- Atau letakkan datasetmu di: {DEFAULT_CSV}\n"
            f"Contoh: python tools/train_and_export_trees_from_csv.py --csv data/contoh.csv"
        )
        print(msg, file=sys.stderr)
        sys.exit(2)
    return path

def main():
    ap = argparse.ArgumentParser(description="Train RandomForest dari CSV dan ekspor pohon keputusan.")
    ap.add_argument("--csv", help=f"Path ke CSV data kebakaran (default: {DEFAULT_CSV} jika ada).")
    ap.add_argument("--outdir", default="model/trees_from_csv", help="Folder output.")
    ap.add_argument("--n-trees", type=int, default=1, help="Jumlah pohon yang diekspor per model.")
    ap.add_argument("--max-depth", type=int, default=4, help="Kedalaman maksimum visualisasi PNG.")
    ap.add_argument("--no-graphviz", action="store_true", help="Matikan ekspor Graphviz (.dot/.png).")
    args = ap.parse_args()

    csv_path = resolve_csv_path(args.csv)
    os.makedirs(args.outdir, exist_ok=True)

    # ====== 1) Load data ======
    df = pd.read_csv(csv_path)

    # Fitur yang dipakai (bisa kamu ubah sesuai kebutuhan dataset)
    features = ["lokasi", "kawasan", "obyek", "penyebab"]  # sertakan 'penyebab' bila ada
    target_air = "air"
    target_mobil = "mobil"

    # Validasi kolom
    missing = [c for c in features + [target_air, target_mobil] if c not in df.columns]
    if missing:
        print(
            f"❌ Kolom berikut tidak ditemukan di CSV: {missing}\n"
            f"Pastikan CSV memiliki: {features + [target_air, target_mobil]}",
            file=sys.stderr,
        )
        sys.exit(2)

    # ====== 2) Bersihkan & siapkan data ======
    for num_col in [target_air, target_mobil, "kerugian", "luas", "jam", "bulan"]:
        if num_col in df.columns:
            df[num_col] = coerce_numeric(df[num_col])

    df_clean = df[features + [target_air, target_mobil]].dropna(subset=[target_air, target_mobil]).copy()

    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X = encoder.fit_transform(df_clean[features])

    y_air = df_clean[target_air].values.astype(float)
    y_mobil = df_clean[target_mobil].values.astype(float)

    # ====== 3) Split ======
    X_train, X_test, y_air_train, y_air_test, y_mobil_train, y_mobil_test = train_test_split(
        X, y_air, y_mobil, test_size=0.2, random_state=42
    )

    # ====== 4) Train ======
    common_params = dict(
        n_estimators=200,
        random_state=42,
        max_depth=10,
        min_samples_leaf=5,
        max_features="sqrt",
        bootstrap=True,
    )
    model_air = RandomForestRegressor(**common_params)
    model_mobil = RandomForestRegressor(**common_params)

    model_air.fit(X_train, y_air_train)
    model_mobil.fit(X_train, y_mobil_train)

    # ====== 5) Evaluasi ======
    y_air_pred = model_air.predict(X_test)
    y_mobil_pred = model_mobil.predict(X_test)
    evaluation = {
        "MAE_air": round(mean_absolute_error(y_air_test, y_air_pred), 3),
        "MSE_air": round(mean_squared_error(y_air_test, y_air_pred), 3),
        "R2_air": round(r2_score(y_air_test, y_air_pred), 3),
        "MAE_mobil": round(mean_absolute_error(y_mobil_test, y_mobil_pred), 3),
        "MSE_mobil": round(mean_squared_error(y_mobil_test, y_mobil_pred), 3),
        "R2_mobil": round(r2_score(y_mobil_test, y_mobil_pred), 3),
        "n_train": int(X_train.shape[0]),
        "n_test": int(X_test.shape[0]),
        "features": features,
        "csv": str(csv_path),
    }

    # ====== 6) Simpan model & evaluasi ======
    bundle_path = os.path.join(args.outdir, "trained_model_from_csv.pkl")
    joblib.dump(
        {"model_air": model_air, "model_mobil": model_mobil, "encoder": encoder, "features": features},
        bundle_path,
    )
    eval_path = os.path.join(args.outdir, "evaluation.json")
    Path(eval_path).write_text(json.dumps(evaluation, indent=2), encoding="utf-8")

    # ====== 7) Ekspor pohon keputusan ======
    def export_some(model, name_prefix):
        n = min(args.n_trees, len(model.estimators_))
        # feature importances
        save_importances_path = os.path.join(args.outdir, f"{name_prefix}_feature_importances.json")
        save_importances(model, features, save_importances_path)
        # trees
        for i in range(n):
            base = os.path.join(args.outdir, f"{name_prefix}_tree_{i}")
            save_tree_text(model.estimators_[i], features, base + ".txt")
            save_tree_png(model.estimators_[i], features, base + ".png", max_depth=args.max_depth)
            if not args.no_graphviz:
                save_tree_graphviz(model.estimators_[i], features, base + "_gv", max_depth=args.max_depth)

    export_some(model_air, "air")
    export_some(model_mobil, "mobil")

    # ====== 8) Ringkasan ke stdout ======
    summary = {
        "bundle_path": bundle_path,
        "evaluation_path": eval_path,
        "outdir": args.outdir,
        "trees_exported_each": int(args.n_trees),
        "png_max_depth": int(args.max_depth),
        "graphviz_used": bool(shutil.which("dot")) and (not args.no_graphviz),
        "evaluation": evaluation,
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
