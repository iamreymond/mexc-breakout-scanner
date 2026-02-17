import requests
import pandas as pd
import os
import time

BASE_URL = "https://api.mexc.com"

# --- Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# --- Fetch all USDT symbols ---
def fetch_usdt_symbols():
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    data = requests.get(url).json()
    symbols = [
        s['symbol'] for s in data['symbols']
        if s['status'] == '1' and s['quoteAsset'] == 'USDT'
    ]
    return symbols

# --- Get top N symbols by 24h quote volume ---
def top_symbols_by_volume(n=5):
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    data = requests.get(url).json()
    usdt = [d for d in data if d['symbol'].endswith('USDT')]
    sorted_usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
    return [s['symbol'] for s in sorted_usdt[:n]]

# --- Fetch previous day candle ---
def fetch_previous_day_candle(symbol):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': '1d', 'limit': 2}  # last 2 days
    data = requests.get(url, params=params).json()
    if not isinstance(data, list) or len(data) < 2:
        return None
    prev_day = data[-2]  # second last = previous day
    prev_high = float(prev_day[2])
    prev_low = float(prev_day[3])
    return prev_high, prev_low

# --- Fetch current price ---
def fetch_current_price(symbol):
    url = f"{BASE_URL}/api/v3/ticker/price"
    params = {'symbol': symbol}
    data = requests.get(url, params=params).json()
    return float(data['price'])

# --- Main ---
def main():
    symbols = top_symbols_by_volume(5)  # top 5 by 24h quote volume
    high_hit = []
    low_hit = []

    for symbol in symbols:
        try:
            prev = fetch_previous_day_candle(symbol)
            if prev is None:
                continue
            prev_high, prev_low = prev

            current_price = fetch_current_price(symbol)

            if current_price >= prev_high:
                high_hit.append(f"{symbol} (price: {current_price} >= prev_high: {prev_high})")
            if current_price <= prev_low:
                low_hit.append(f"{symbol} (price: {current_price} <= prev_low: {prev_low})")

            time.sleep(0.2)  # avoid API rate limit

        except Exception as e:
            print(f"Error {symbol}: {e}")

    # Prepare Telegram message
    message = "🔥 MEXC Top 5 Coins — Previous Daily High/Low Hit\n\n"
    if high_hit:
        message += "✅ Hit Previous High:\n" + "\n".join(high_hit) + "\n\n"
    if low_hit:
        message += "🔻 Hit Previous Low:\n" + "\n".join(low_hit) + "\n\n"
    if not high_hit and not low_hit:
        message += "No coins hit previous daily high or low."

    send_telegram(message)
    print("Test complete. Telegram message sent.")

if __name__ == "__main__":
    main()
