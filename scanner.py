import os
import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_klines(symbol):
    symbol = symbol.replace("USDT", "-USDT")

    url = f"https://api.kucoin.com/api/v1/market/candles?type=1hour&symbol={symbol}"

    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        raise Exception(f"API Hatası: {r.text}")

    data = r.json()

    if data.get("code") != "200000":
        raise Exception(f"KuCoin Hatası: {data}")

    candles = data["data"]

    rows = []

    for c in candles:
        rows.append([
            float(c[2]),  # open
            float(c[3]),  # close
            float(c[4]),  # high
            float(c[5]),  # low
            float(c[6])   # volume
        ])

    df = pd.DataFrame(
        rows,
        columns=["open", "close", "high", "low", "volume"]
    )

    df = df[::-1].reset_index(drop=True)

    return df


def score_coin(symbol):
    try:
        df = get_klines(symbol)

        if len(df) < 50:
            return None

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
            "price": round(df["close"].iloc[-1], 6)
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

results = sorted(
    results,
    key=lambda x: x["score"],
    reverse=True
)[:3]

message = "🚀 EN İYİ 3 FIRSAT\n\n"

if len(results) == 0:
    message += "Uygun coin bulunamadı."
else:
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
