import requests
import pandas as pd
import os
import time
import json
from datetime import datetime, timedelta

BASE_URL = "https://api.mexc.com"
TOP_LIMIT = 200
MEMORY_FILE = "pair_memory.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==============================
# TELEGRAM (Safe GET)
# ==============================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# ==============================
# MEMORY FOR PAIRED SCAN
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

def clear_memory(pair):
    memory = load_memory()
    memory[pair] = []
    save_memory(memory)

# ==============================
# DETERMINE CURRENT PAIR SESSION
# ==============================
def get_current_pair():
    now = datetime.utcnow()
    hour = now.hour
    minute = now.minute

    # Paired sessions (UTC for GitHub cron)
    # MORNING: 8:30AM & 9:00AM PHT => 0:30 & 1:00 UTC
    # NOON: 12:30PM & 1:00PM PHT => 4:30 & 5:00 UTC
    # AFTERNOON: 4:30PM & 5:00PM PHT => 8:30 & 9:00 UTC
    # EVENING: 8:30PM & 9:00PM PHT => 12:30 & 13:00 UTC
    if (hour == 0 and minute >= 30) or hour == 1:
        return "MORNING", minute >= 30
    if (hour == 4 and minute >= 30) or hour == 5:
        return "NOON", minute >= 30
    if (hour == 8 and minute >= 30) or hour == 9:
        return "AFTERNOON", minute >= 30
    if (hour == 12 and minute >= 30) or hour == 13:
        return "EVENING", minute >= 30
    return "UNKNOWN", False

# ==============================
# FETCH TOP 200 USDT COINS
# ==============================
def top_symbols_by_volume(n=TOP_LIMIT):
    url = f"{BASE_URL}/api/v3/ticker/24hr"
    data = requests.get(url).json()
    if not isinstance(data, list):
        return []

    usdt = [d for d in data if d['symbol'].endswith('USDT')]
    sorted_usdt = sorted(usdt, key=lambda x: float(x['quoteVolume']), reverse=True)
    return [s['symbol'] for s in sorted_usdt[:n]]

# ==============================
# FETCH LAST 2 4H CANDLES
# ==============================
def fetch_klines(symbol, interval='4h', limit=2):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    data = requests.get(url, params=params).json()
    if not isinstance(data, list) or len(data) < 2:
        return None

    df = pd.DataFrame(
        data,
        columns=['timestamp','open','high','low','close','volume',
                 'close_time','quote_volume','num_trades','taker_buy_base',
                 'taker_buy_quote','ignore']
    )
    df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
    return df

# ==============================
# MAIN
# ==============================
def main():
    pair, is_first_minute = get_current_pair()
    if pair == "UNKNOWN":
        print("Not a scheduled session. Exiting.")
        return

    # Clear memory for pair if first run in the pair (e.g., 8:30 AM or 12:30 PM)
    if is_first_minute:
        clear_memory(pair)

    memory = load_memory()
    previous_coins = memory.get(pair, [])

    bearish_rev = []
    bullish_rev = []

    symbols = top_symbols_by_volume(TOP_LIMIT)

    for symbol in symbols:
        df = fetch_klines(symbol)
        if df is None:
            continue

        prev = df.iloc[-2]
        current = df.iloc[-1]

        # Bearish reversal: swept previous high, closed below
        if current['high'] > prev['high'] and current['close'] < prev['high']:
            if symbol not in previous_coins:
                bearish_rev.append(symbol)

        # Bullish reversal: swept previous low, closed above
        elif current['low'] < prev['low'] and current['close'] > prev['low']:
            if symbol not in previous_coins:
                bullish_rev.append(symbol)

        time.sleep(0.03)

    # Update memory for this pair
    all_now = previous_coins + bearish_rev + bullish_rev
    memory[pair] = all_now
    save_memory(memory)

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    message = f"🔥 MEXC 4H Reversal Scan (Top {TOP_LIMIT})\n\n"
    message += f"Session: {pair}\nTime: {now_str}\n\n"

    message += "🔻 Bearish Reversal\n" + ("\n".join(bearish_rev) if bearish_rev else "None")
    message += "\n\n🔺 Bullish Reversal\n" + ("\n".join(bullish_rev) if bullish_rev else "None")

    send_telegram(message)
    print("Scan complete. Telegram sent.")

if __name__ == "__main__":
    main()
