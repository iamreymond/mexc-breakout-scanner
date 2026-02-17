import os
import requests

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fast test: only 2 coins
symbols = ["BTCUSDT", "ETHUSDT"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def test_scan():
    message = "🔥 MEXC Scanner Test\n\n"
    for symbol in symbols:
        # Fake detection for testing
        message += f"{symbol}: Test OK ✅\n"
    send_telegram(message)

if __name__ == "__main__":
    test_scan()
