import os
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": "🤖 XAU SIGNAL ARY\n\nBot berhasil online di Railway.\nStatus: ACTIVE"
}

requests.post(url, data=payload)

print("Pesan terkirim")
