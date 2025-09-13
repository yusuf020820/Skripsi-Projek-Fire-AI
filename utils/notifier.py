import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()  # Load .env

# Ambil kredensial dari environment
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_FROM")
TO_WHATSAPP = os.getenv("TWILIO_WHATSAPP_TO")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def kirim_wa(nama, lokasi, obyek, air, mobil):
    try:
        pesan = (
            f"🔥 *Laporan Kebakaran Baru!*\n\n"
            f"👤 Nama: {nama}\n"
            f"📍 Lokasi: {lokasi}\n"
            f"🔥 Obyek: {obyek}\n\n"
            f"💧 Prediksi Air: {air} m³\n"
            f"🚒 Prediksi Armada: {mobil} unit"
        )

        message = client.messages.create(
            body=pesan,
            from_=FROM_WHATSAPP,
            to=TO_WHATSAPP
        )

        print("✅ Pesan berhasil dikirim ke WhatsApp")
    except Exception as e:
        print(f"❌ Gagal kirim WA: {e}")
