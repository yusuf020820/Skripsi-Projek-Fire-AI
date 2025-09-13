import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import time

def simpan_ke_google_sheet(nama, lokasi, obyek, air, mobil):
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        cred_path = os.path.join(base_dir, 'gsheet-cred.json')

        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open("PrediksiKebakaran").sheet1

        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [waktu, nama, lokasi, obyek, air, mobil]

        # Tambahkan data
        sheet.append_row(row)

        # 🔴 Tambahkan jeda agar commit dulu ke Google Sheet
        time.sleep(2)

        # Hitung baris total
        last_row = len(sheet.get_all_values()) + 1

        # Sisipkan baris kosong
        sheet.insert_row([""] * len(row), last_row)

        print("✅ Data berhasil dikirim + baris kosong disisipkan!")

    except Exception as e:
        print(f"❌ Gagal menyimpan ke Google Sheet: {e}")
