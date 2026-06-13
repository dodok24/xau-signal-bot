import os
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")

# Ambil harga emas terbaru
url_data = (
    f"https://api.twelvedata.com/price"
    f"?symbol=XAU/USD"
    f"&apikey={API_KEY}"
)

response = requests.get(url_data)
data = response.json()

if "price" in data:

    price = data["price"]

    message = f"""
🤖 XAU SIGNAL ARY

Status : ACTIVE

XAUUSD Live Price
{price}
"""

else:

    message = f"""
⚠️ XAU SIGNAL ARY

Gagal mengambil data market.

Response:
{data}
"""

telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    telegram_url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(message)
