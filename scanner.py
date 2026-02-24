import requests
import pandas as pd
import os
import time
import json

BASE_URL = "https://api.binance.com"
TOP_LIMIT = 200
MEMORY_FILE = "pair_memory.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==============================
# TELEGRAM (OLD SAFE STYLE)
# ==============================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={
        "chat_id": CHAT_ID,
        "text": message
    })


# ==============================
# MEMORY
# ==============================
def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)


# ==============================
# FETCH TOP 200
# ==============================
def get_top_symbols(limit=200):
    r = requests.get(f"{BASE_URL}/api/v3/ticker/24hr")
    data = r.json()

    usdt = [d for d in data if d['symbol'].endswith('USDT')]
    sorted_usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)

    return [s['symbol'] for s in sorted_usdt[:limit]]


# ==============================
# FETCH 4H
# ==============================
def fetch_klines(symbol):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': '4h', 'limit': 2}
    data = requests.get(url, params=params).json()

    if not isinstance(data, list) or len(data) < 2:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            'timestamp','open','high','low','close','volume',
            'close_time','quote_asset_volume',
            'num_trades','taker_buy_base','taker_buy_quote','ignore'
        ]
    )

    df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
    return df


# ==============================
# MAIN
# ==============================
def main():
    memory = load_memory()
    last_sent = memory.get("last_scan", [])

    bearish_rev = []
    bullish_rev = []

    symbols = get_top_symbols(TOP_LIMIT)

    for symbol in symbols:
        df = fetch_klines(symbol)
        if df is None:
            continue

        prev = df.iloc[-2]
        current = df.iloc[-1]

        # Bearish reversal
        if current['high'] > prev['high'] and current['close'] < prev['high']:
            if symbol not in last_sent:
                bearish_rev.append(symbol)

        # Bullish reversal
        elif current['low'] < prev['low'] and current['close'] > prev['low']:
            if symbol not in last_sent:
                bullish_rev.append(symbol)

        time.sleep(0.03)

    all_now = bearish_rev + bullish_rev
    memory["last_scan"] = all_now
    save_memory(memory)

    message = "🔥 Binance 4H Reversal (Top 200)\n\n"

    if bearish_rev:
        message += "🔻 Bearish Reversal:\n" + "\n".join(bearish_rev) + "\n\n"
    if bullish_rev:
        message += "🔺 Bullish Reversal:\n" + "\n".join(bullish_rev) + "\n\n"
    if not bearish_rev and not bullish_rev:
        message += "No signals."

    send_telegram(message)
    print("Scan complete. Telegram sent.")


if __name__ == "__main__":
    main()
