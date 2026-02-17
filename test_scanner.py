import requests
import pandas as pd
import os

BASE_URL = "https://api.mexc.com"

# --- Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# --- Fetch top USDT symbols (limit top 5 for testing) ---
def fetch_mexc_symbols(limit=5):
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    data = requests.get(url).json()
    symbols = [
        s['symbol'] for s in data['symbols']
        if s['status'] == '1' and s['quoteAsset'] == 'USDT'
    ]
    return symbols[:limit]

# --- Fetch last N daily klines ---
def fetch_klines(symbol, interval='1d', limit=3):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    data = requests.get(url, params=params).json()
    if not isinstance(data, list) or len(data) == 0:
        return None
    df = pd.DataFrame(
        data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume']
    )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df.astype(float)

# --- Main test function ---
def main():
    symbols = fetch_mexc_symbols(limit=5)
    high_hit = []
    low_hit = []

    for symbol in symbols:
        try:
            df = fetch_klines(symbol)
            if df is None or len(df) < 2:
                continue

            prev = df.iloc[-2]   # previous daily candle
            latest = df.iloc[-1] # latest daily candle

            # Check if high touched previous high
            if latest['high'] >= prev['high']:
                high_hit.append(symbol)

            # Check if low touched previous low
            if latest['low'] <= prev['low']:
                low_hit.append(symbol)

        except Exception as e:
            print(f"Error: {symbol} - {e}")

    # Prepare message
    message = "🔥 MEXC Top 5 Coins — Daily High/Low Test\n\n"
    if high_hit:
        message += "✅ Tapped Previous High:\n" + "\n".join(high_hit) + "\n\n"
    if low_hit:
        message += "🔻 Tapped Previous Low:\n" + "\n".join(low_hit) + "\n\n"
    if not high_hit and not low_hit:
        message += "No coins tapped previous high or low."

    # Send to Telegram
    send_telegram(message)
    print("Test complete. Message sent to Telegram.")

if __name__ == "__main__":
    main()
