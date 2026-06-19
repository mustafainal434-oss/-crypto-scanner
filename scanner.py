import os
import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=100"
    r = requests.get(url).json()

    df = pd.DataFrame(r, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbav","tqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

def score_coin(symbol):
    try:
        df = get_klines(symbol)

        ema20 = EMAIndicator(df["close"], window=20).ema_indicator()
        ema50 = EMAIndicator(df["close"], window=50).ema_indicator()
        rsi = RSIIndicator(df["close"], window=14).rsi()

        score = 0

        if ema20.iloc[-1] > ema50.iloc[-1]:
            score += 40

        if 45 < rsi.iloc[-1] < 65:
            score += 30

        avg_vol = df["volume"].tail(20).mean()

        if df["volume"].iloc[-1] > avg_vol:
            score += 30

        return {
            "symbol": symbol,
            "score": score,
            "price": round(df["close"].iloc[-1], 4)
        }

    except:
        return None

coins = []

with open("coins.txt") as f:
    for line in f:
        coin = line.strip().upper()
        if coin:
            coins.append(coin)

results = []

for coin in coins:
    r = score_coin(coin)
    if r:
        results.append(r)

results = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

message = "🚀 EN İYİ 3 FIRSAT\n\n"

for i, coin in enumerate(results, start=1):
    message += (
        f"{i}. {coin['symbol']}\n"
        f"Puan: {coin['score']}/100\n"
        f"Fiyat: {coin['price']}\n\n"
    )

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(message)
