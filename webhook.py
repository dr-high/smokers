import os
import json
import sqlite3
import traceback
from flask import Flask, request

from dotenv import load_dotenv
import requests

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

app = Flask(__name__)

@app.route("/paystack_webhook", methods=["POST"])
def paystack_webhook():
    try:
        data = request.get_json()
        if not data:
            return "Invalid Data", 400

        reference = data["data"].get("reference", "No reference")
        amount = data["data"].get("amount", 0) / 100
        status = data["data"].get("status", "unknown")
        user_id = data["data"]["metadata"].get("user_id", "unknown")
        address = data["data"]["metadata"].get("address", "No address")
        phone = data["data"]["metadata"].get("phone", "No phone")

        payment_verified, amount, status, user_id = verify_paystack_payment(reference)
        if payment_verified:
            save_order(user_id, reference, amount, address, phone, status)
            return "Webhook processed successfully", 200
        else:
            return "Payment verification failed", 400

    except Exception as e:
        traceback.print_exc()
        return "Internal Server Error", 500

def save_order(user_id, reference, amount, address, phone, status):
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (user_id, reference, amount, address, phone, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, reference, amount, address, phone, status))
    conn.commit()
    conn.close()

def verify_paystack_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response.status_code == 200 and response_json.get("status") and response_json["data"]["status"] == "success":
        amount = response_json["data"]["amount"] / 100
        user_id = response_json["data"]["metadata"].get("user_id", "unknown")
        return True, amount, "success", user_id
    return False, 0, "failed", "unknown"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
