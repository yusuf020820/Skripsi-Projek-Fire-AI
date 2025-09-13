

import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetLogger:
    def __init__(self, sheet_name: str, cred_filename: str = 'gsheet-cred.json'):#ganti gsheet-cred.json dengan nama folder yang ada di secrete

       
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.normpath(os.path.join(base_dir, '..', 'secrets', cred_filename))

       
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
        client = gspread.authorize(creds)
        self.sheet = client.open(sheet_name).sheet1

    def simpan_laporan(self, data: dict) -> bool:
        
        try:
            row = [
                data.get("tanggal", datetime.now().strftime("%Y-%m-%d")),
                data.get("jam", datetime.now().strftime("%H:%M")),
                data.get("nama", ""),
                data.get("lokasi", ""),
                data.get("obyek", ""),
                data.get("air", ""),
                data.get("mobil", "")
            ]
            self.sheet.append_row(row, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            print(f" Gagal menyimpan ke Google Sheet: {e}")
            return False
