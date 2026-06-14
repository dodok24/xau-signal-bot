import os
import requests
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")

url = (
    f"https://api.twelvedata.com/time_series"
    f"?symbol=XAU/USD"
    f"&interval=5min"
    f"&outputsize=100"
    f"&apikey={API_KEY}"
)

r = requests.get(url)
data = r.json()

if "values" not in data:
    print("Data gagal")
    exit()

df = pd.DataFrame(data["values"])

df["close"] = df["close"].astype(float)
df = df[::-1]

price = df["close"].iloc[-1]

ema20 = df["close"].ewm(span=20).mean().iloc[-1]
ema50 = df["close"].ewm(span=50).mean().iloc[-1]

# TREND
if ema20 > ema50:
    trend = "BULLISH"
else:
    trend = "BEARISH"

# CONFIDENCE
confidence = 0

if ema20 > ema50:
    confidence += 30

distance = abs(price - ema20)

if distance < 2:
    confidence += 20

if price > ema20:
    confidence += 20

if abs(ema20 - ema50) > 1:
    confidence += 30

# GRADE
if confidence >= 90:
    grade = "PREMIUM"
elif confidence >= 80:
    grade = "A+"
elif confidence >= 70:
    grade = "A"
elif confidence >= 60:
    grade = "WATCHLIST"
else:
    grade = "NO TRADE"

# ATR SEDERHANA
atr = abs(df["close"].diff()).rolling(14).mean().iloc[-1]

sl_buy = price - atr * 1.5
tp1_buy = price + atr * 2
tp2_buy = price + atr * 4

sl_sell = price + atr * 1.5
tp1_sell = price - atr * 2
tp2_sell = price - atr * 4

# SIGNAL
signal = "NO TRADE"

if trend == "BULLISH" and confidence >= 70:
    signal = "BUY"

if trend == "BEARISH" and confidence >= 70:
    signal = "SELL"

# MESSAGE
if signal == "BUY":

    message = f"""
🚀 XAU ARY SCAN

📈 SIGNAL : BUY

Price : {price:.2f}

SL : {sl_buy:.2f}
TP1 : {tp1_buy:.2f}
TP2 : {tp2_buy:.2f}

Confidence : {confidence}%
Grade : {grade}
"""

elif signal == "SELL":

    message = f"""
🚀 XAU ARY SCAN

📉 SIGNAL : SELL

Price : {price:.2f}

SL : {sl_sell:.2f}
TP1 : {tp1_sell:.2f}
TP2 : {tp2_sell:.2f}

Confidence : {confidence}%
Grade : {grade}
"""

else:

    message = f"""
🚀 XAU ARY SCAN

Status : NO TRADE

Price : {price:.2f}

Trend : {trend}

Confidence : {confidence}%
Grade : {grade}
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
