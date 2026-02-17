import requests
import pandas as pd
import os
import time

BASE_URL = "https://api.mexc.com"

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# Fetch last N daily candles
def fetch_klines(symbol, interval='1d', limit=3):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    data = requests.get(url, params=params).json()
    if not isinstance(data, list) or len(data) < 2:
        return None
    df = pd.DataFrame(
        data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume']
    )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df.astype(float)

# Get top N coins by 24h volume (all USDT coins)
def top_symbols_by_volume(n=100):
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    data = requests.get(url).json()
    usdt = [d for d in data if d['symbol'].endswith('USDT')]

    # Sort by 24h quote volume
    sorted_usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
    return [s['symbol'] for s in sorted_usdt[:n]]

# Main
def main():
    symbols = top_symbols_by_volume(100)  # top 100 coins
    high_hit = []
    low_hit = []

    for symbol in symbols:
        try:
            df = fetch_klines(symbol, "1d", 3)
            if df is None or len(df) < 2:
                continue

            prev = df.iloc[-2]   # previous day
            latest = df.iloc[-1] # latest candle

            # Compare with previous day
            if latest['high'] >= prev['high']:
                high_hit.append(symbol)
            if latest['low'] <= prev['low']:
                low_hit.append(symbol)

            time.sleep(0.2)  # avoid rate limit

        except Exception as e:
            print(f"Error: {symbol} - {e}")

    # Prepare Telegram message
    message = "🔥 MEXC Top 100 Coins — Previous Daily High/Low Hit\n\n"
    if high_hit:
        message += "✅ Hit Previous High:\n" + "\n".join(high_hit) + "\n\n"
    if low_hit:
        message += "🔻 Hit Previous Low:\n" + "\n".join(low_hit) + "\n\n"
    if not high_hit and not low_hit:
        message += "No coins hit previous daily high or low."

    send_telegram(message)
    print("Scan complete. Telegram message sent.")

if __name__ == "__main__":
    main()
