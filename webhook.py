import os
import json
from flask import Flask, request
import requests
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Details
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "6009484587"  # Replace with your Telegram ID

# Flask App
app = Flask(__name__)

# Webhook Route
@app.route("/paystack_webhook", methods=["POST"])
def paystack_webhook():
    data = request.get_json()
    if not data:
        return "Invalid Data", 400

    # Verify Paystack signature (Optional but recommended)
    paystack_secret = "sk_test_2ab162c82e50d96fa701b593bc72689be1d17456"
    received_signature = request.headers.get("X-Paystack-Signature")
    expected_signature = paystack_secret  # For simplicity, we're not hashing, but you should verify it.

    if received_signature != expected_signature:
        return "Unauthorized", 401

    # Extract necessary details
    event = data.get("event")
    amount = data["data"]["amount"] / 100  # Convert kobo to GHS
    status = data["data"]["status"]
    user_id = data["data"]["metadata"]["user_id"]

    # Notify Admin via Telegram
    message = f"🚀 *Paystack Payment Received!*\n\n👤 User ID: {user_id}\n💰 Amount: GHS {amount}\n✅ Status: {status}"
    send_telegram_message(message)

    return "Webhook received", 200

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=data)

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)