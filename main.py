import os
import time
import requests
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")


def send_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )


def get_data(symbol, interval="5min", size=100):

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}"
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


def scan_symbol(symbol):

    df = get_data(symbol)

    if df is None:
        return f"""
[{symbol}]

DATA ERROR
"""

    price = df["close"].iloc[-1]

    ema20 = df["close"].ewm(span=20).mean().iloc[-1]
    ema50 = df["close"].ewm(span=50).mean().iloc[-1]

    score = 0

    if ema20 > ema50:
        score += 55

    if price > ema20:
        score += 20

    distance = abs(price - ema20)

    if distance < (price * 0.001):
        score += 15

    score += 10

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

    return f"""
[{symbol}]

Price : {price:.2f}

EMA20 : {ema20:.2f}
EMA50 : {ema50:.2f}

Score : {score}
Grade : {grade}
"""


def run_scan():

    try:

        xau_report = scan_symbol("XAU/USD")
        btc_report = scan_symbol("BTC/USD")

        message = f"""
🚀 XAU SIGNAL ARY

{xau_report}

------------------------

{btc_report}

Status : SCANNING
"""

        send_telegram(message)

        print(message)

    except Exception as e:

        send_telegram(
            f"⚠️ XAU SIGNAL ARY ERROR\n\n{str(e)}"
        )

        print(str(e))


while True:

    run_scan()

    print("Menunggu 5 menit...")

    time.sleep(300)
