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

# Webhook Route (EXPLICITLY allowing only POST)
@app.route("/paystack_webhook", methods=["POST"])
def paystack_webhook():
    if request.method != "POST":
        return "Method Not Allowed", 405  # Explicitly return error for non-POST requests

    data = request.get_json()
    if not data:
        return "Invalid Data", 400

    # Extract details
    event = data.get("event", "")
    amount = data["data"].get("amount", 0) / 100  # Convert kobo to GHS
    status = data["data"].get("status", "unknown")
    user_id = data["data"]["metadata"].get("user_id", "unknown")

    # Notify Admin via Telegram
    message = f"🚀 *Paystack Payment Received!*\n\n👤 User ID: {user_id}\n💰 Amount: GHS {amount}\n✅ Status: {status}"
    send_telegram_message(message)

    return "Webhook received successfully", 200

@app.route("/", methods=["GET"])
def home():
    return "Webhook is running!", 200  # Simple homepage for testing

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=data)

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
