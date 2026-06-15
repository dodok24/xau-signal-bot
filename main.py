import os
import time
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_DATA_API_KEY")

SYMBOL = "XAU/USD"

last_signal = None
last_bos_level = None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=15
    )


def get_data(symbol, interval="5min", size=200):

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={symbol}"
        f"&interval={interval}"
        f"&outputsize={size}"
        f"&apikey={API_KEY}"
    )

    data = requests.get(url, timeout=20).json()

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


def get_trend():

    df_h1 = get_data(
        SYMBOL,
        "1h",
        200
    )

    if df_h1 is None:
        return "NONE"

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
        return "BULLISH"

    if ema20 < ema50:
        return "BEARISH"

    return "NONE"


def find_swings(df):

    swing_highs = []
    swing_lows = []

    for i in range(2, len(df) - 2):

        high = df["high"].iloc[i]

        if (
            high > df["high"].iloc[i - 1]
            and high > df["high"].iloc[i - 2]
            and high > df["high"].iloc[i + 1]
            and high > df["high"].iloc[i + 2]
        ):
            swing_highs.append(
                (i, high)
            )

        low = df["low"].iloc[i]

        if (
            low < df["low"].iloc[i - 1]
            and low < df["low"].iloc[i - 2]
            and low < df["low"].iloc[i + 1]
            and low < df["low"].iloc[i + 2]
        ):
            swing_lows.append(
                (i, low)
            )

    return swing_highs, swing_lows


def detect_structure(
    swing_highs,
    swing_lows
):

    if (
        len(swing_highs) < 2
        or len(swing_lows) < 2
    ):
        return "NONE"

    last_high = swing_highs[-1][1]
    prev_high = swing_highs[-2][1]

    last_low = swing_lows[-1][1]
    prev_low = swing_lows[-2][1]

    if (
        last_high > prev_high
        and last_low > prev_low
    ):
        return "HHHL"

    if (
        last_high < prev_high
        and last_low < prev_low
    ):
        return "LHLL"

    return "NONE"


def detect_bos(
    df,
    swing_highs,
    swing_lows
):

    close_price = (
        df["close"].iloc[-1]
    )

    if len(swing_highs) > 0:

        level = swing_highs[-1][1]

        if close_price > level:

            return (
                "BULLISH",
                level
            )

    if len(swing_lows) > 0:

        level = swing_lows[-1][1]

        if close_price < level:

            return (
                "BEARISH",
                level
            )

    return (
        "NONE",
        None
    )


def momentum_valid(df):

    candle = df.iloc[-1]

    body = abs(
        candle["close"]
        - candle["open"]
    )

    rng = (
        candle["high"]
        - candle["low"]
    )

    if rng == 0:
        return False

    ratio = body / rng

    return ratio >= 0.6


def snr_valid(
    price,
    swing_highs,
    swing_lows,
    atr
):

    if (
        len(swing_highs) < 3
        or len(swing_lows) < 3
    ):
        return False

    resistance = sum(
        x[1]
        for x in swing_highs[-3:]
    ) / 3

    support = sum(
        x[1]
        for x in swing_lows[-3:]
    ) / 3

    dist_res = (
        resistance - price
    )

    dist_sup = (
        price - support
    )

    if (
        dist_res > 0
        and dist_res < atr
    ):
        return False

    if (
        dist_sup > 0
        and dist_sup < atr
    ):
        return False

    return True


def send_signal(
    signal,
    price,
    atr,
    structure,
    bos_level
):

    now = datetime.now()

    if signal == "BUY":

        sl = (
            price
            - (atr * 1.5)
        )

        tp1 = (
            price
            + (atr * 2)
        )

        tp2 = (
            price
            + (atr * 4)
        )

        tp3 = (
            price
            + (atr * 6)
        )

    else:

        sl = (
            price
            + (atr * 1.5)
        )

        tp1 = (
            price
            - (atr * 2)
        )

        tp2 = (
            price
            - (atr * 4)
        )

        tp3 = (
            price
            - (atr * 6)
        )

    message = f"""
🚀 XAU ARY V4

Tanggal : {now.strftime('%d-%m-%Y')}
Jam      : {now.strftime('%H:%M:%S')}

Pair     : XAU/USD

SIGNAL   : {signal}

Entry    : {price:.2f}

SL       : {sl:.2f}

TP1      : {tp1:.2f}
TP2      : {tp2:.2f}
TP3      : {tp3:.2f}

Structure : {structure}
BOS Level : {bos_level:.2f}

Status    : NEW SETUP
"""

    send_telegram(message)

    print(message)


def scan():

    global last_signal
    global last_bos_level

    df = get_data(SYMBOL)

    if df is None:
        return

    trend = get_trend()

    if trend == "NONE":
        return

    atr = calculate_atr(df)

    price = df["close"].iloc[-1]

    swing_highs, swing_lows = (
        find_swings(df)
    )

    structure = detect_structure(
        swing_highs,
        swing_lows
    )

    bos_type, bos_level = (
        detect_bos(
            df,
            swing_highs,
            swing_lows
        )
    )

    if not momentum_valid(df):
        return

    if not snr_valid(
        price,
        swing_highs,
        swing_lows,
        atr
    ):
        return

    if (
        trend == "BULLISH"
        and structure == "HHHL"
        and bos_type == "BULLISH"
    ):

        if (
            last_signal == "BUY"
            and last_bos_level == bos_level
        ):
            return

        last_signal = "BUY"
        last_bos_level = bos_level

        send_signal(
            "BUY",
            price,
            atr,
            structure,
            bos_level
        )

    if (
        trend == "BEARISH"
        and structure == "LHLL"
        and bos_type == "BEARISH"
    ):

        if (
            last_signal == "SELL"
            and last_bos_level == bos_level
        ):
            return

        last_signal = "SELL"
        last_bos_level = bos_level

        send_signal(
            "SELL",
            price,
            atr,
            structure,
            bos_level
        )


while True:

    try:

        scan()

    except Exception as e:

        print(e)

    time.sleep(60)
