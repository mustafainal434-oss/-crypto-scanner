import os
import requests
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_klines(symbol):
    try:
        symbol = symbol.replace("USDT", "-USDT")

        url = f"https://api.kucoin.com/api/v1/market/candles?type=1hour&symbol={symbol}"

        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")

        data = r.json()

        if data.get("code") != "200000":
            raise Exception(data)

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

    except Exception as e:
        print(f"HATA -> {symbol}: {e}")
        return None


def score_coin(symbol):
    try:
        df = get_klines(symbol)

        if df is None:
            return None

        if len(df) < 200:
            return None

        ema20 = EMAIndicator(
            close=df["close"],
            window=20
        ).ema_indicator()

        ema50 = EMAIndicator(
            close=df["close"],
            window=50
        ).ema_indicator()

        ema200 = EMAIndicator(
            close=df["close"],
            window=200
        ).ema_indicator()

        rsi = RSIIndicator(
            close=df["close"],
            window=14
        ).rsi()

        score = 0

        # Trend
        if ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
            score += 40

        # RSI
        if 50 <= rsi.iloc[-1] <= 70:
            score += 30

        # Hacim
        avg_vol = df["volume"].tail(20).mean()

        if df["volume"].iloc[-1] > avg_vol * 1.5:
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

with open("coins.txt", "r") as f:
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

results = [x for x in results if x["score"] >= 70]

results = sorted(
    results,
    key=lambda x: x["score"],
    reverse=True
)[:5]

message = "🚀 GÜÇLÜ LONG ADAYLARI\n\n"

if len(results) == 0:
    message += "Bugün güçlü sinyal bulunamadı."

else:
    for i, coin in enumerate(results, start=1):

        entry = coin["price"]
        stop = round(entry * 0.97, 6)
        tp = round(entry * 1.06, 6)

        message += (
            f"{i}. {coin['symbol']}\n"
            f"Giriş: {entry}\n"
            f"Stop: {stop}\n"
            f"Hedef: {tp}\n"
            f"Güven: {coin['score']}/100\n\n"
        )

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(message)
