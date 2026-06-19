import requests

coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

for symbol in coins:
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=60&limit=5"

        r = requests.get(url, timeout=15)

        print("\n" + "=" * 50)
        print("COIN:", symbol)
        print("STATUS:", r.status_code)
        print("CEVAP:")
        print(r.text[:1000])
        print("=" * 50)

    except Exception as e:
        print("HATA:", e)
