import os
import json
import sqlite3
from flask import Flask, request

from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

def verify_paystack_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    response = requests.get(url, headers=headers).json()
    if response.get("status") and response["data"]["status"] == "success":
        return True, response["data"]["amount"] / 100, response["data"]["metadata"]
    return False, 0, {}

@app.route("/paystack_webhook", methods=["POST"])
def paystack_webhook():
    data = request.get_json()
    if not data:
        return "Invalid Data", 400

    reference = data["data"].get("reference")
    amount = data["data"].get("amount", 0) / 100
    metadata = data["data"].get("metadata", {})
    user_id = metadata.get("user_id", "unknown")
    address = metadata.get("address", "")
    phone = metadata.get("phone", "")

    verified, amount, metadata = verify_paystack_payment(reference)
    if verified:
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, status, address, phone, reference) VALUES (?, ?, ?, 'paid', ?, ?, ?)", 
                       (user_id, 1, 1, address, phone, reference))
        conn.commit()
        conn.close()
        return "Webhook processed", 200
    return "Verification failed", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
