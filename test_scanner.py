import os
import requests
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# Get top 5 USDT pairs by 24h quote volume
def get_top5_symbols():
    url = "https://api.mexc.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    usdt = [d for d in data if d["symbol"].endswith("USDT")]
    sorted_pairs = sorted(usdt, key=lambda v: float(v["quoteVolume"]), reverse=True)
    return [s["symbol"] for s in sorted_pairs[:5]]

# Fetch last 2 daily bars
def fetch_daily_klines(symbol):
    url = "https://api.mexc.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": 2}
    return requests.get(url, params=params).json()

# Get current price
def fetch_price(symbol):
    url = "https://api.mexc.com/api/v3/ticker/price"
    params = {"symbol": symbol}
    return float(requests.get(url, params=params).json()["price"])

def main():
    symbols = get_top5_symbols()

    above = []
    below = []

    for symbol in symbols:
        try:
            klines = fetch_daily_klines(symbol)
            if not isinstance(klines, list) or len(klines) < 2:
                continue

            prev = klines[-2]
            prev_high = float(prev[2])
            prev_low = float(prev[3])

            current = fetch_price(symbol)

            # Check hit/tap
            if current >= prev_high:
                above.append((symbol, current, prev_high))
            if current <= prev_low:
                below.append((symbol, current, prev_low))

            time.sleep(0.2)  # avoid API limit

        except Exception as e:
            print(f"Error {symbol}: {e}")

    message = "🔥 MEXC Top 5 Breakout Test\n\n"
    if above:
        message += "Hit Previous Daily High:\n"
        for s,c,h in above:
            message += f"{s} price:{c} >= high:{h}\n"
        message += "\n"

    if below:
        message += "Hit Previous Daily Low:\n"
        for s,c,l in below:
            message += f"{s} price:{c} <= low:{l}\n"
        message += "\n"

    if not above and not below:
        message += "No hits in top 5."

    send_telegram(message)


if __name__ == "__main__":
    main()
