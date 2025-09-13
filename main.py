# main.py (Flask backend + pywebview)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from core.data_source import SheetReader
from core.predictor import FirePredictor
from core.logger import GoogleSheetLogger
from core.notifier import WhatsAppNotifier
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "fireai-secret"

# Init komponen
base_dir = os.path.dirname(__file__)
model_path = os.path.join(base_dir, "model", "trained_model_Dummy.pkl")
predictor = FirePredictor(model_path)
logger = GoogleSheetLogger(sheet_name=os.getenv("GSHEET_NAME","PrediksiKebakaran"))
notifier = WhatsAppNotifier()
sr = SheetReader()

# Helpers ringkas
def get_kawasan_count():
    df = sr.get_dataframe()
    if df.empty: return {}
    vc = (df["Kawasan"].fillna("Lainnya").astype(str).str.strip().value_counts())
    return vc.to_dict()

def get_bulanan_count():
    df = sr.get_dataframe()
    if df.empty or "Waktu_dt" not in df.columns: return {}
    df = df.dropna(subset=["Waktu_dt"])
    df["BulanLabel"] = df["Waktu_dt"].dt.strftime("%Y-%m")
    vc = df["BulanLabel"].value_counts().sort_index()
    return vc.to_dict()

def get_kecamatan_count():
    df = sr.get_dataframe()
    if df.empty: return {}
    vc = df["Kecamatan"].fillna("Lainnya").astype(str).str.strip().value_counts()
    return vc.to_dict()

def get_kecamatan_options():
    df = sr.get_dataframe()
    if df.empty: return []
    return sorted([k for k in df["Kecamatan"].dropna().astype(str).unique()])

@app.route("/", methods=["GET","POST"])
def index():
    hasil = None
    if request.method == "POST":
        try:
            hasil = predictor.predict(request.form)
        except Exception as e:
            flash(f"Gagal memproses prediksi: {e}", "error")

    df = sr.get_dataframe()
    laporan = df.to_dict(orient="records") if not df.empty else []
    pie_data = get_kecamatan_count()      # ganti: per kecamatan
    bar_data = get_bulanan_count()        # tetap
    kecamatan_opts = get_kecamatan_options()

    return render_template("dashboard.html",
                           hasil=hasil, laporan=laporan,
                           pie_data=pie_data, bar_data=bar_data,
                           kecamatan_opts=kecamatan_opts)

@app.route("/api/stats")
def api_stats():
    period  = request.args.get("period","month")     # day|month|year
    kec     = request.args.get("kecamatan")          # baru
    alamat  = request.args.get("alamat")             # baru (substring)
    obyek   = request.args.get("obyek")              # opsional lama

    agg = sr.aggregate(by=period, kecamatan=kec, alamat_contains=alamat, obyek=obyek)
    return jsonify({
        "labels": agg["label"].astype(str).tolist(),
        "values": agg["count"].astype(int).tolist()
    })

@app.route("/submit", methods=["POST"])
def submit():
    nama   = request.form.get("nama")
    lokasi = request.form.get("lokasi")
    obyek  = request.form.get("obyek")

    if not nama or not lokasi or not obyek:
        flash("Semua field wajib diisi!", "error")
        return redirect(url_for("index"))

    now = datetime.now()
    bulan = now.month

    try:
        hasil = predictor.predict({
            "lokasi": lokasi,
            "kawasan": "umum",
            "obyek": obyek.strip().lower(),
            "bulan": int(bulan),
        })
    except Exception as e:
        app.logger.exception("Exception saat memanggil predictor.predict")
        flash(f"Gagal memproses prediksi: {e}", "error")
        return redirect(url_for("index"))

    # === tangani error dari predictor ===
    if isinstance(hasil, dict) and "error" in hasil:
        flash(f"Gagal prediksi: {hasil['error']}", "error")
        return redirect(url_for("index"))

    #validasi format hasil
    if (not isinstance(hasil, dict)
        or "air" not in hasil
        or "mobil" not in hasil):
        app.logger.error("Format hasil prediksi tidak sesuai: %r", hasil)
        flash("Format hasil prediksi tidak valid.", "error")
        return redirect(url_for("index"))

    try:
        air = float(hasil["air"])
        mobil = int(round(float(hasil["mobil"])))
    except Exception as e:
        app.logger.exception("Tipe hasil prediksi tidak bisa dikonversi: %r", hasil)
        flash(f"Prediksi tidak dapat dibaca: {e}", "error")
        return redirect(url_for("index"))
    air, mobil = hasil["air"], hasil["mobil"]

    try:
        logger.simpan_laporan({
            "tanggal": now.strftime("%Y-%m-%d %H:%M"),
            "nama": nama, "lokasi": lokasi, "obyek": obyek,
            "bulan": bulan, "air": air, "mobil": mobil
        })
    except Exception as e:
        flash(f"Gagal mencatat ke Google Sheet: {e}", "error")

    pesan = (
        "*Laporan Kebakaran Masuk*\n"
        f"Nama Pelapor : {nama}\n"
        f"Lokasi       : {lokasi}\n"
        f"Obyek        : {obyek}\n"
        f"Prediksi Air : {air} m³\n"
        f"Prediksi Mobil: {mobil} unit\n"
        f"Waktu        : {now.strftime('%Y-%m-%d %H:%M')}"
    )
    try:
        notifier.kirim_pesan(pesan)
    except Exception as e:
        flash(f"Gagal kirim ke WhatsApp: {e}", "error")

    flash(f"Prediksi berhasil: Air {air} m³, Mobil {mobil} unit", "success")
    return redirect(url_for("index"))

@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static","favicon.ico", mimetype="image/x-icon")

if __name__ == "__main__":
    from threading import Thread
    import webview

    def start_flask():
        app.run()

    t = Thread(target=start_flask, daemon=True)
    t.start()
    webview.create_window("Command Center Dashboard", "http://127.0.0.1:5000", width=1100, height=720)
    webview.start()
