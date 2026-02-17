import requests
import pandas as pd
import os

BASE_URL = "https://api.mexc.com"

# --- Telegram Function ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# --- Fetch MEXC Symbols ---
def fetch_mexc_symbols(limit=5):
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    data = requests.get(url).json()
    symbols = [
        s['symbol'] for s in data['symbols']
        if s['status'] == '1' and s['quoteAsset'] == 'USDT'
    ]
    # Optional: sort by symbol name (or use volume API later)
    return symbols[:limit]

# --- Fetch Klines ---
def fetch_klines(symbol, interval, limit):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    data = requests.get(url, params=params).json()
    if not isinstance(data, list) or len(data) == 0:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'close_time', 'quote_volume'
        ]
    )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df.astype(float)

# --- Main Test ---
def main():
    symbols = fetch_mexc_symbols(limit=5)
    results = {"tapped_high": [], "tapped_low": []}

    for symbol in symbols:
        try:
            df = fetch_klines(symbol, "1d", 3)
            if df is None or len(df) < 2:
                continue

            prev = df.iloc[-2]
            latest = df.iloc[-1]

            # Check if high touched previous high
            if latest['high'] >= prev['high']:
                results["tapped_high"].append(symbol)

            # Check if low touched previous low
            if latest['low'] <= prev['low']:
                results["tapped_low"].append(symbol)

        except Exception as e:
            print(f"Error: {symbol} - {e}")

    # Prepare Telegram message
    message = "🔥 MEXC Top 5 Coins — Daily High/Low Test\n\n"
    if results["tapped_high"]:
        message += "Tapped Previous High:\n" + "\n".join(results["tapped_high"]) + "\n\n"
    if results["tapped_low"]:
        message += "Tapped Previous Low:\n" + "\n".join(results["tapped_low"]) + "\n\n"
    if not results["tapped_high"] and not results["tapped_low"]:
        message += "No coins tapped previous high or low."

    send_telegram(message)
    print("Test complete. Message sent to Telegram.")

if __name__ == "__main__":
    main()
