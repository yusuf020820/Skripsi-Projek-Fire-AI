import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.notifier import WhatsAppNotifier

wa = WhatsAppNotifier()

pesan = "hoka"

wa.kirim_pesan(pesan)
