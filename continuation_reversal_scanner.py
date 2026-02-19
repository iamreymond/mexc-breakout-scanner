import requests
import pandas as pd
import os
import time

# ==============================
# BINANCE CONFIG
# ==============================

BASE_URL = "https://api.binance.com"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==============================
# TELEGRAM
# ==============================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})


# ==============================
# FETCH ALL RANKED SYMBOLS
# ==============================

def get_all_ranked_symbols():
    # Exchange Info
    r = requests.get(f"{BASE_URL}/api/v3/exchangeInfo")
    exchange_info = r.json()

    if 'symbols' not in exchange_info:
        print("Error fetching exchangeInfo:", exchange_info)
        return []

    trading_symbols = [
        s['symbol'] for s in exchange_info['symbols']
        if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT'
    ]

    # 24h ticker for ranking
    r2 = requests.get(f"{BASE_URL}/api/v3/ticker/24hr")
    ticker_24h = r2.json()

    if not isinstance(ticker_24h, list):
        print("Error fetching ticker:", ticker_24h)
        return []

    usdt_data = [
        d for d in ticker_24h
        if d['symbol'] in trading_symbols
    ]

    sorted_usdt = sorted(
        usdt_data,
        key=lambda x: float(x['quoteVolume']),
        reverse=True
    )

    # Return ranked list
    return [(rank + 1, s['symbol']) for rank, s in enumerate(sorted_usdt)]


# ==============================
# FETCH DAILY CANDLES
# ==============================

def fetch_klines(symbol, interval='1d', limit=4):
    url = f"{BASE_URL}/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    data = requests.get(url, params=params).json()

    if not isinstance(data, list) or len(data) < 3:
        return None

    df = pd.DataFrame(
        data,
        columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume',
            'num_trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ]
    )

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    return df.astype(float)


# ==============================
# MAIN LOGIC
# ==============================

def main():

    ranked_symbols = get_all_ranked_symbols()

    if not ranked_symbols:
        send_telegram("Error fetching Binance symbols.")
        return

    bullish_cont = []
    bearish_cont = []
    bullish_rev = []
    bearish_rev = []

    for rank, symbol in ranked_symbols:

        try:
            df = fetch_klines(symbol, "1d", 4)
            if df is None or len(df) < 3:
                continue

            base = df.iloc[-3]      # Candle #1
            prev = df.iloc[-2]      # Candle #2
            today = df.iloc[-1]     # Candle #3

            base_high = base['high']
            base_low = base['low']

            # ======================
            # CONTINUATION
            # ======================

            if prev['close'] > base_high and today['close'] > base_high:
                bullish_cont.append(f"{rank}. {symbol}")

            if prev['close'] < base_low and today['close'] < base_low:
                bearish_cont.append(f"{rank}. {symbol}")

            # ======================
            # REVERSAL
            # ======================

            if (prev['high'] > base_high and
                base_low < prev['close'] < base_high):
                bearish_rev.append(f"{rank}. {symbol}")

            if (prev['low'] < base_low and
                base_low < prev['close'] < base_high):
                bullish_rev.append(f"{rank}. {symbol}")

            time.sleep(0.1)  # avoid rate limit

        except Exception as e:
            print(f"Error: {symbol} - {e}")

    # ==============================
    # TELEGRAM MESSAGE
    # ==============================

    message = "🔥 Binance — Continuation & Reversal Scan\n\n"

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
