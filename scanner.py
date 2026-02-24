import requests
import pandas as pd
import time
import os
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.binance.com"
TOP_LIMIT = 200
MEMORY_FILE = "pair_memory.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==============================
# TIME SESSION DETECTION (PHT)
# ==============================
def get_session():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    pht_now = utc_now.astimezone(timezone(timedelta(hours=8)))

    hour = pht_now.hour
    minute = pht_now.minute

    if hour == 8 and minute >= 30 or hour == 9:
        return "MORNING_1", "8:30 AM / 9:00 AM"

    if hour == 12 and minute >= 30 or hour == 13:
        return "NOON", "12:30 PM / 1:00 PM"

    if hour == 16 and minute >= 30 or hour == 17:
        return "AFTERNOON", "4:30 PM / 5:00 PM"

    if hour == 20 and minute >= 30 or hour == 21:
        return "EVENING", "8:30 PM / 9:00 PM"

    return None, None


# ==============================
# TELEGRAM
# ==============================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    response = requests.post(url, data=payload)
    print("Telegram Status:", response.status_code)
    print("Telegram Response:", response.text)


# ==============================
# MEMORY HANDLING
# ==============================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)


# ==============================
# FETCH TOP 200
# ==============================
def get_top_symbols(limit=200):
    r = requests.get(f"{BASE_URL}/api/v3/exchangeInfo", timeout=10)
    exchange_info = r.json()

    trading_symbols = {
        s['symbol']
        for s in exchange_info['symbols']
        if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT'
    }

    r2 = requests.get(f"{BASE_URL}/api/v3/ticker/24hr", timeout=10)
    ticker_24h = r2.json()

    usdt_data = [
        d for d in ticker_24h
        if d['symbol'] in trading_symbols
    ]

    sorted_usdt = sorted(
        usdt_data,
        key=lambda x: float(x['quoteVolume']),
        reverse=True
    )

    return [s['symbol'] for s in sorted_usdt[:limit]]


# ==============================
# FETCH 4H CANDLES
# ==============================
def fetch_klines(symbol):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': '4h', 'limit': 2}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if len(data) < 2:
        return None

    df = pd.DataFrame(data, columns=[
        'timestamp','open','high','low','close','volume',
        'close_time','quote_asset_volume',
        'num_trades','taker_buy_base','taker_buy_quote','ignore'
    ])

    df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
    return df


# ==============================
# MAIN
# ==============================
def main():
    session_key, session_label = get_session()
    if not session_key:
        print("Not a scheduled session.")
        return

    memory = load_memory()
    previous_coins = memory.get(session_key, [])

    bearish_rev = []
    bullish_rev = []

    symbols = get_top_symbols(TOP_LIMIT)

    for symbol in symbols:
        df = fetch_klines(symbol)
        if df is None:
            continue

        prev = df.iloc[-2]
        current = df.iloc[-1]

        # Bearish Reversal
        if current['high'] > prev['high'] and current['close'] < prev['high']:
            if symbol not in previous_coins:
                bearish_rev.append(symbol)

        # Bullish Reversal
        elif current['low'] < prev['low'] and current['close'] > prev['low']:
            if symbol not in previous_coins:
                bullish_rev.append(symbol)

        time.sleep(0.03)

    all_current = bearish_rev + bullish_rev
    memory[session_key] = all_current
    save_memory(memory)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    message = f"🔥 <b>4H Reversal Scan (Top {TOP_LIMIT})</b>\n\n"
    message += f"Session: {session_label}\n"
    message += f"Time: {now}\n\n"

    message += "🔻 Bearish Reversal\n"
    message += "\n".join(bearish_rev) if bearish_rev else "None"
    message += "\n\n🔺 Bullish Reversal\n"
    message += "\n".join(bullish_rev) if bullish_rev else "None"

    send_telegram(message)
    print("Scan sent.")


if __name__ == "__main__":
    main()
