import requests
import os
from datetime import datetime

MEXC_BASE = "https://api.mexc.com"
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


def get_market_caps():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1
    }
    data = requests.get(COINGECKO_URL, params=params).json()
    return {coin["symbol"].upper(): coin["market_cap"] for coin in data}


def fetch_symbols():
    url = f"{MEXC_BASE}/api/v3/exchangeInfo"
    data = requests.get(url).json()
    return [
        s["symbol"]
        for s in data["symbols"]
        if s["status"] == "1" and s["quoteAsset"] == "USDT"
    ]


def fetch_klines(symbol):
    url = f"{MEXC_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": 2}
    data = requests.get(url, params=params).json()
    if not isinstance(data, list) or len(data) < 2:
        return None
    return data


def fetch_price(symbol):
    url = f"{MEXC_BASE}/api/v3/ticker/price"
    params = {"symbol": symbol}
    data = requests.get(url, params=params).json()
    return float(data["price"])


def main():
    symbols = fetch_symbols()
    market_caps = get_market_caps()

    above = []
    below = []

    for symbol in symbols:
        try:
            klines = fetch_klines(symbol)
            if not klines:
                continue

            prev = klines[-2]
            prev_high = float(prev[2])
            prev_low = float(prev[3])

            current_price = fetch_price(symbol)

            base_symbol = symbol.replace("USDT", "")
            market_cap = market_caps.get(base_symbol, 0)

            if current_price > prev_high:
                above.append((symbol, market_cap))

            if current_price < prev_low:
                below.append((symbol, market_cap))

        except:
            continue

    # Sort by market cap (high → low)
    above.sort(key=lambda x: x[1], reverse=True)
    below.sort(key=lambda x: x[1], reverse=True)

    message = "🔥 MEXC Daily Breakout Scan\n\n"

    if above:
        message += "Above Previous High:\n"
        message += "\n".join([x[0] for x in above])
        message += "\n\n"

    if below:
        message += "Below Previous Low:\n"
        message += "\n".join([x[0] for x in below])
        message += "\n\n"

    if not above and not below:
        message += "No breakout detected."

    send_telegram(message)


if __name__ == "__main__":
    main()
