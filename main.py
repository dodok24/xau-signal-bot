import os
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")

url_data = (
    f"https://api.twelvedata.com/time_series"
    f"?symbol=XAU/USD"
    f"&interval=5min"
    f"&outputsize=50"
    f"&apikey={API_KEY}"
)

response = requests.get(url_data)
data = response.json()

if "values" in data:

    closes = [float(c["close"]) for c in data["values"]]

    price = closes[0]

    ema20 = sum(closes[:20]) / 20
    ema50 = sum(closes[:50]) / 50

    trend = "BULLISH" if ema20 > ema50 else "BEARISH"

    confidence = 70

    grade = "WATCHLIST"

    if confidence >= 75:
        grade = "B"

    if confidence >= 80:
        grade = "A"

    if confidence >= 85:
        grade = "A+"

    if confidence >= 90:
        grade = "PREMIUM"

    message = f"""
📊 XAU ARY SCAN

Price : {price}

Trend : {trend}

EMA20 : {round(ema20,2)}
EMA50 : {round(ema50,2)}

Confidence : {confidence}%
Grade : {grade}

Status : SCANNING
"""

else:

    message = f"""
⚠️ XAU ARY

Gagal mengambil data market

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
