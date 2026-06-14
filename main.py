import os
import requests
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")


def get_data(interval, size=100):
    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol=XAU/USD"
        f"&interval={interval}"
        f"&outputsize={size}"
        f"&apikey={API_KEY}"
    )

    data = requests.get(url).json()

    if "values" not in data:
        return None

    df = pd.DataFrame(data["values"])

    df["close"] = df["close"].astype(float)

    df = df[::-1].reset_index(drop=True)

    return df


df5 = get_data("5min")
df15 = get_data("15min")
df60 = get_data("1h")

if df5 is None or df15 is None or df60 is None:
    print("Data gagal")
    exit()

# ======================
# PRICE
# ======================

price = df5["close"].iloc[-1]

# ======================
# EMA H1
# ======================

ema20_h1 = df60["close"].ewm(span=20).mean().iloc[-1]
ema50_h1 = df60["close"].ewm(span=50).mean().iloc[-1]

# ======================
# EMA M15
# ======================

ema20_m15 = df15["close"].ewm(span=20).mean().iloc[-1]
ema50_m15 = df15["close"].ewm(span=50).mean().iloc[-1]

# ======================
# EMA M5
# ======================

ema20_m5 = df5["close"].ewm(span=20).mean().iloc[-1]

# ======================
# SCORE
# ======================

score = 0

# H1 trend
if ema20_h1 > ema50_h1:
    score += 30

# M15 trend
if ema20_m15 > ema50_m15:
    score += 25

# M5 momentum
if price > ema20_m5:
    score += 20

# Retest EMA20
distance = abs(price - ema20_m5)

if distance < 2:
    score += 15

# Volatility
atr = abs(df5["close"].diff()).rolling(14).mean().iloc[-1]

if atr > 0:
    score += 10

# ======================
# GRADE
# ======================

if score >= 90:
    grade = "PREMIUM"
elif score >= 80:
    grade = "A+"
elif score >= 70:
    grade = "A"
elif score >= 60:
    grade = "WATCHLIST"
else:
    grade = "NO TRADE"

# ======================
# SIGNAL
# ======================

signal = "NO TRADE"

bull_h1 = ema20_h1 > ema50_h1
bear_h1 = ema20_h1 < ema50_h1

bull_m15 = ema20_m15 > ema50_m15
bear_m15 = ema20_m15 < ema50_m15

if bull_h1 and bull_m15 and score >= 70:
    signal = "BUY"

if bear_h1 and bear_m15 and score >= 70:
    signal = "SELL"

# ======================
# SL TP
# ======================

sl_buy = price - atr * 1.5
tp1_buy = price + atr * 2
tp2_buy = price + atr * 4
tp3_buy = price + atr * 6

sl_sell = price + atr * 1.5
tp1_sell = price - atr * 2
tp2_sell = price - atr * 4
tp3_sell = price - atr * 6

# ======================
# MESSAGE
# ======================

if signal == "BUY":

    message = f"""
🚀 XAU ARY SIGNAL

📈 BUY

Price : {price:.2f}

SL : {sl_buy:.2f}

TP1 : {tp1_buy:.2f}
TP2 : {tp2_buy:.2f}
TP3 : {tp3_buy:.2f}

Score : {score}
Grade : {grade}
"""

elif signal == "SELL":

    message = f"""
🚀 XAU ARY SIGNAL

📉 SELL

Price : {price:.2f}

SL : {sl_sell:.2f}

TP1 : {tp1_sell:.2f}
TP2 : {tp2_sell:.2f}
TP3 : {tp3_sell:.2f}

Score : {score}
Grade : {grade}
"""

else:

    message = f"""
⚠️ XAU ARY

NO TRADE

Price : {price:.2f}

Score : {score}
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
