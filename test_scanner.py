import os
import requests
import pandas as pd

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Telegram function ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# --- Top 5 coins for testing ---
TEST_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]

# --- Fake candlestick data for testing ---
def fetch_fake_klines(symbol):
    # Simulated last two daily candles
    data = [
        {"timestamp": 1, "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
        {"timestamp": 2, "open": 105, "high": 115, "low": 100, "close": 116, "volume": 1200}  # closes above previous high
    ]
    df = pd.DataFrame(data)
    df.set_index("timestamp", inplace=True)
    return df

# --- Main scanner test ---
def main():
    results = {"above_daily_high": [], "below_daily_low": []}

    for symbol in TEST_COINS:
        df = fetch_fake_klines(symbol)
        prev = df.iloc[-2]
        latest = df.iloc[-1]

        if latest["close"] > prev["high"]:
            results["above_daily_high"].append(symbol)
        if latest["close"] < prev["low"]:
            results["below_daily_low"].append(symbol)

    # Prepare Telegram message
    message = "🔥 MEXC Breakout Scanner — TEST\n\n"
    if results["above_daily_high"]:
        message += "Above Previous High:\n" + "\n".join(results["above_daily_high"]) + "\n\n"
    if results["below_daily_low"]:
        message += "Below Previous Low:\n" + "\n".join(results["below_daily_low"]) + "\n\n"
    if not results["above_daily_high"] and not results["below_daily_low"]:
        message += "No breakout detected in test."

    send_telegram(message)

if __name__ == "__main__":
    main()
