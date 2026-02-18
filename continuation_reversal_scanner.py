import requests
import pandas as pd
import os
import time

BASE_URL = "https://api.mexc.com"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

def fetch_klines(symbol, interval='1d', limit=4):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    data = requests.get(url, params=params).json()

    if not isinstance(data, list) or len(data) < 3:
        return None

    df = pd.DataFrame(
        data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume']
    )

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df.astype(float)

def top_symbols_by_volume(n=100):
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    data = requests.get(url).json()
    usdt = [d for d in data if d['symbol'].endswith('USDT')]
    sorted_usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
    return [s['symbol'] for s in sorted_usdt[:n]]

def main():
    symbols = top_symbols_by_volume(100)

    bullish_cont = []
    bearish_cont = []
    bullish_rev = []
    bearish_rev = []

    for symbol in symbols:
        try:
            df = fetch_klines(symbol, "1d", 4)
            if df is None or len(df) < 3:
                continue

            base = df.iloc[-3]      # Candle #1
            prev = df.iloc[-2]      # Candle #2 (closed)
            today = df.iloc[-1]     # Candle #3 (current)

            base_high = base['high']
            base_low = base['low']

            # ======================
            # CONTINUATION
            # ======================

            # Bullish continuation
            if prev['close'] > base_high and today['close'] > base_high:
                bullish_cont.append(symbol)

            # Bearish continuation
            if prev['close'] < base_low and today['close'] < base_low:
                bearish_cont.append(symbol)

            # ======================
            # REVERSAL
            # ======================

            # Bearish reversal (upper sweep)
            if (prev['high'] > base_high and
                base_low < prev['close'] < base_high):
                bearish_rev.append(symbol)

            # Bullish reversal (lower sweep)
            if (prev['low'] < base_low and
                base_low < prev['close'] < base_high):
                bullish_rev.append(symbol)

            time.sleep(0.2)

        except Exception as e:
            print(f"Error: {symbol} - {e}")

    message = "🔥 MEXC Top 100 — Continuation & Reversal Scan\n\n"

    if bullish_cont:
        message += "🟢 Bullish Continuation:\n" + "\n".join(bullish_cont) + "\n\n"
    if bearish_cont:
        message += "🔴 Bearish Continuation:\n" + "\n".join(bearish_cont) + "\n\n"
    if bullish_rev:
        message += "🔵 Bullish Reversal:\n" + "\n".join(bullish_rev) + "\n\n"
    if bearish_rev:
        message += "🟣 Bearish Reversal:\n" + "\n".join(bearish_rev) + "\n\n"

    if not any([bullish_cont, bearish_cont, bullish_rev, bearish_rev]):
        message += "No setups found."

    send_telegram(message)
    print("Scan complete.")

if __name__ == "__main__":
    main()
