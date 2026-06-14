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


def run_scan():

    try:

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol=XAU/USD"
            f"&interval=5min"
            f"&outputsize=100"
            f"&apikey={API_KEY}"
        )

        data = requests.get(url).json()

        if "values" not in data:
            send_telegram(f"⚠️ Data error\n\n{data}")
            return

        df = pd.DataFrame(data["values"])

        df["close"] = df["close"].astype(float)

        df = df[::-1].reset_index(drop=True)

        price = df["close"].iloc[-1]

        ema20 = df["close"].ewm(span=20).mean().iloc[-1]
        ema50 = df["close"].ewm(span=50).mean().iloc[-1]

        score = 0

        if ema20 > ema50:
            score += 55

        if price > ema20:
            score += 20

        distance = abs(price - ema20)

        if distance < 2:
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

        message = f"""
🚀 XAU ARY SCAN

Price : {price:.2f}

EMA20 : {ema20:.2f}
EMA50 : {ema50:.2f}

Score : {score}
Grade : {grade}

Status : SCANNING
"""

        send_telegram(message)

        print(message)

    except Exception as e:

        send_telegram(f"⚠️ ERROR\n\n{str(e)}")


while True:

    run_scan()

    print("Menunggu 5 menit...")

    time.sleep(300)
