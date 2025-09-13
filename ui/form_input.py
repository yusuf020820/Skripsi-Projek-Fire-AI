import tkinter as tk
from tkinter import ttk, messagebox
from logic.predict import predict_kebutuhan
from datetime import datetime

def run_form():
    root = tk.Tk()
    root.title("🔥 FireAI - Prediksi Kebakaran")
    root.geometry("600x350")
    root.configure(bg="#f8f9fa")

    style = ttk.Style()
    style.configure("TLabel", font=("Segoe UI", 10), background="#f8f9fa")
    style.configure("TButton", font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    form_frame = ttk.Frame(frame)
    form_frame.grid(row=0, column=0, sticky="n", padx=(0, 20))

    ttk.Label(form_frame, text="📋 Input Laporan", style="Title.TLabel").grid(row=0, column=0, columnspan=2, pady=10)

    ttk.Label(form_frame, text="Nama Pelapor").grid(row=1, column=0, sticky="w", pady=5)
    entry_nama = ttk.Entry(form_frame, width=30)
    entry_nama.grid(row=1, column=1, pady=5)

    ttk.Label(form_frame, text="Lokasi Kejadian").grid(row=2, column=0, sticky="w", pady=5)
    entry_lokasi = ttk.Entry(form_frame, width=30)
    entry_lokasi.grid(row=2, column=1, pady=5)

    ttk.Label(form_frame, text="Objek Terbakar").grid(row=3, column=0, sticky="w", pady=5)
    entry_obyek = ttk.Entry(form_frame, width=30)
    entry_obyek.grid(row=3, column=1, pady=5)

    result_frame = ttk.Frame(frame)
    result_frame.grid(row=0, column=1, sticky="n")

    ttk.Label(result_frame, text="🧾 Hasil Prediksi", style="Title.TLabel").grid(row=0, column=0, pady=10)
    label_air = ttk.Label(result_frame, text="Air: -", font=("Segoe UI", 12))
    label_air.grid(row=1, column=0, pady=5)
    label_mobil = ttk.Label(result_frame, text="Mobil: -", font=("Segoe UI", 12))
    label_mobil.grid(row=2, column=0, pady=5)

    def on_predict():
        nama = entry_nama.get()
        lokasi = entry_lokasi.get()
        obyek = entry_obyek.get()

        if not all([nama, lokasi, obyek]):
            messagebox.showerror("❌ Error", "Semua data wajib diisi.")
            return

        # Ambil waktu sekarang
        now = datetime.now()
        jam = now.hour
        bulan = now.month

        # Prediksi
        result = predict_kebutuhan(lokasi, "umum", obyek, jam, bulan) 

        if isinstance(result[0], str) and result[1] is None:
            messagebox.showerror("❌ Error", result[0])
        else:
            air, mobil = result
            label_air.config(text=f"💧 Air: {air} m³")
            label_mobil.config(text=f"🚒 Mobil: {mobil} unit")

    ttk.Button(form_frame, text="🔮 Prediksi", command=on_predict).grid(row=4, column=0, columnspan=2, pady=10)

    root.mainloop()
