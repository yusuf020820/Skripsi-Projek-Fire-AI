import os
from dotenv import load_dotenv
from twilio.rest import Client

class WhatsAppNotifier:
    def __init__(self):
        load_dotenv()
        self.sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.token = os.getenv("TWILIO_AUTH_TOKEN")
        self.sender = os.getenv("TWILIO_FROM")
        self.receiver = os.getenv("TWILIO_TO")
        self.client = Client(self.sid, self.token)

    def kirim_pesan(self, pesan: str) -> bool:
        try:
            message = self.client.messages.create(
                from_=self.sender,
                to=self.receiver,
                body=pesan
            )
            print(f"✅ Pesan terkirim. SID: {message.sid}")
            return True
        except Exception as e:
            print(f" Gagal kirim pesan: {str(e)}")
            return False
