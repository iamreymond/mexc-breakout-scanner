import os
import requests

# GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

test_message = "Hello! This is a test from GitHub Actions."

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
params = {"chat_id": CHAT_ID, "text": test_message}

response = requests.get(url, params=params)
print(response.text)
