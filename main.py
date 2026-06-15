import os
import time
import requests
import pandas as pd
from datetime import datetime

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


def get_data(symbol, interval="5min", size=200):

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

    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)

    df = df[::-1].reset_index(drop=True)

    return df


def calculate_atr(df, period=14):

    high_low = df["high"] - df["low"]

    high_close = abs(
        df["high"] - df["close"].shift()
    )

    low_close = abs(
        df["low"] - df["close"].shift()
    )

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(period).mean()

    return atr.iloc[-1]


def get_trend_score(symbol):

    df_h1 = get_data(symbol, "1h", 200)

    if df_h1 is None:
        return 0, "UNKNOWN"

    ema20 = (
        df_h1["close"]
        .ewm(span=20)
        .mean()
        .iloc[-1]
    )

    ema50 = (
        df_h1["close"]
        .ewm(span=50)
        .mean()
        .iloc[-1]
    )

    if ema20 > ema50:
        return 20, "BULLISH"

    elif ema20 < ema50:
        return 20, "BEARISH"

    return 0, "SIDEWAYS"


def get_momentum_score(df):

    candle = df.iloc[-1]

    body = abs(
        candle["close"] -
        candle["open"]
    )

    candle_range = (
        candle["high"] -
        candle["low"]
    )

    if candle_range == 0:
        return 0

    ratio = body / candle_range

    if ratio >= 0.6:
        return 30

    elif ratio >= 0.4:
        return 15

    return 0


def scan_symbol(symbol):

    df = get_data(symbol)

    if df is None:
        return None

    price = df["close"].iloc[-1]

    ema20 = (
        df["close"]
        .ewm(span=20)
        .mean()
        .iloc[-1]
    )

    ema50 = (
        df["close"]
        .ewm(span=50)
        .mean()
        .iloc[-1]
    )

    atr = calculate_atr(df)

    trend_score, trend = get_trend_score(symbol)

    momentum_score = get_momentum_score(df)

    pullback_score = 0

    if abs(price - ema20) < atr:
        pullback_score = 20

    atr_score = 10 if atr > 0 else 0

    score = (
        trend_score +
        momentum_score +
        pullback_score +
        atr_score
    )

    if score >= 90:
        grade = "PREMIUM"

    elif score >= 80:
        grade = "A+"

    elif score >= 70:
        grade = "A"

    else:
        grade = "NO TRADE"

    signal = "NO TRADE"

    if score >= 70:

        if trend == "BULLISH":
            signal = "BUY"

            entry = price
            sl = price - (atr * 1.5)
            tp1 = price + (atr * 2)
            tp2 = price + (atr * 4)
            tp3 = price + (atr * 6)

        elif trend == "BEARISH":
            signal = "SELL"

            entry = price
            sl = price + (atr * 1.5)
            tp1 = price - (atr * 2)
            tp2 = price - (atr * 4)
            tp3 = price - (atr * 6)

        else:
            return None

        now = datetime.now()

        return f"""
🚀 XAU SIGNAL ARY

Tanggal : {now.strftime('%d-%m-%Y')}
Jam      : {now.strftime('%H:%M:%S')}

Pair     : {symbol}

SIGNAL   : {signal}

Entry    : {entry:.2f}

SL       : {sl:.2f}

TP1      : {tp1:.2f}
TP2      : {tp2:.2f}
TP3      : {tp3:.2f}

Trend        : {trend}
Trend Score  : {trend_score}
Momentum     : {momentum_score}
Pullback     : {pullback_score}
ATR Filter   : {atr_score}

Score        : {score}
Grade        : {grade}
"""

    return None


def run_scan():

    try:

        for symbol in [
            "XAU/USD",
            "BTC/USD"
        ]:

            result = scan_symbol(symbol)

            if result:
                send_telegram(result)
                print(result)

    except Exception as e:

        error_msg = (
            f"⚠️ XAU SIGNAL ARY ERROR\n\n{str(e)}"
        )

        send_telegram(error_msg)

        print(error_msg)


while True:

    run_scan()

    print("Scanning...")

    time.sleep(300)
