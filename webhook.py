import os
import json
from flask import Flask, request, redirect
import requests
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Details
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = "6009484587"  # Replace with your actual Telegram ID

# Flask App
app = Flask(__name__)

# Paystack Secret Key (for verifying transactions)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# Webhook Route
@app.route("/paystack_webhook", methods=["POST", "GET"])
def paystack_webhook():
    if request.method == "GET":
        # Paystack is redirecting user after payment
        reference = request.args.get("reference", "No reference provided")

        # ✅ Step 1: Verify Payment Before Redirecting
        payment_verified, amount, status, user_id = verify_paystack_payment(reference)

        if payment_verified:
            # ✅ Step 2: Notify the user about successful payment
            message = f"🎉 *Payment Successful!*\n\n💰 Amount: GHS {amount}\n✅ Status: {status}\n🔗 Reference: `{reference}`"
            send_telegram_message(user_id, message)

            # ✅ Step 3: Redirect User to Telegram Bot with a Success Message
            telegram_redirect_url = f"https://t.me/drhighspecialBot?start=payment_{reference}"
            return redirect(telegram_redirect_url, code=302)
        else:
            return "Payment verification failed. Please contact support.", 400

    elif request.method == "POST":
        # Paystack sends a POST request with transaction details
        data = request.get_json()
        if not data:
            return "Invalid Data", 400

        # Extract details
        reference = data["data"].get("reference", "No reference")
        amount = data["data"].get("amount", 0) / 100  # Convert kobo to GHS
        status = data["data"].get("status", "unknown")
        user_id = data["data"]["metadata"].get("user_id", "unknown")

        # ✅ Notify Admin
        admin_message = f"🚀 *New Payment Received!*\n\n👤 User ID: {user_id}\n💰 Amount: GHS {amount}\n✅ Status: {status}\n🔗 Reference: `{reference}`"
        send_telegram_message(ADMIN_CHAT_ID, admin_message)

        # ✅ Log Event
        print(f"✅ Payment Processed: {reference} | Amount: {amount} | Status: {status}")

        return "Webhook processed successfully", 200

@app.route("/", methods=["GET"])
def home():
    return "Webhook is running!", 200

def send_telegram_message(chat_id, message):
    """Send message to Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=data)
        response_json = response.json()

        if response.status_code == 200 and response_json.get("ok"):
            print("✅ Telegram message sent successfully!")
            return True
        else:
            print(f"❌ Telegram Error: {response_json}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram Request Failed: {e}")
        return False

def verify_paystack_payment(reference):
    """Verify transaction with Paystack API before confirming it."""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response.status_code == 200 and response_json.get("status") and response_json["data"]["status"] == "success":
            amount = response_json["data"]["amount"] / 100  # Convert kobo to GHS
            user_id = response_json["data"]["metadata"].get("user_id", "unknown")
            return True, amount, "success", user_id
        else:
            return False, 0, "failed", "unknown"

    except requests.exceptions.RequestException as e:
        print(f"❌ Paystack Verification Failed: {e}")
        return False, 0, "failed", "unknown"

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
