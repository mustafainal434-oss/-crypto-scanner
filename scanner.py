import os
import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_klines(symbol):
    url = (
        f"https://api.bybit.com/v5/market/kline"
        f"?category=linear&symbol={symbol}&interval=60&limit=100"
    )

    r = requests.get(url, timeout=10)
    data = r.json()

    if data["retCode"] != 0:
        raise Exception(data.get("retMsg", "Bybit Hatası"))

    rows = data["result"]["list"]

    df = pd.DataFrame(
        rows,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
        ],
    )

    df = df.iloc[::-1].reset_index(drop=True)

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
        direction = "NÖTR"

        if ema20.iloc[-1] > ema50.iloc[-1]:
            score += 40
            direction = "LONG"

        if ema20.iloc[-1] < ema50.iloc[-1]:
            score += 40
            direction = "SHORT"

        if 45 < rsi.iloc[-1] < 65:
            score += 30

        avg_vol = df["volume"].tail(20).mean()

        if df["volume"].iloc[-1] > avg_vol:
            score += 30

        return {
            "symbol": symbol,
            "score": score,
            "price": round(df["close"].iloc[-1], 4),
            "direction": direction,
        }

    except Exception as e:
        print(f"HATA -> {symbol}: {e}")
        return None


coins = []

with open("coins.txt") as f:
    for line in f:
        coin = line.strip().upper()

        if coin:
            coins.append(coin)

print(f"{len(coins)} coin yüklendi")

results = []

for coin in coins:
    result = score_coin(coin)

    if result:
        results.append(result)

print(f"Başarılı coin sayısı: {len(results)}")

results = sorted(results, key=lambda x: x["score"], reverse=True)

top3 = results[:3]

message = "🚀 EN İYİ 3 FIRSAT\n\n"

if len(top3) == 0:
    message += "Uygun coin bulunamadı."
else:
    medals = ["🥇", "🥈", "🥉"]

    for i, coin in enumerate(top3):
        message += (
            f"{medals[i]} {coin['symbol']}\n"
            f"Yön: {coin['direction']}\n"
            f"Puan: {coin['score']}/100\n"
            f"Fiyat: {coin['price']}\n\n"
        )

print(message)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)
