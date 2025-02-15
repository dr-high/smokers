import os
import traceback
import json
from flask import Flask, request, redirect
import requests
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Details
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Flask App
app = Flask(__name__)

# Paystack Secret Key (for verifying transactions)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# Webhook Route
@app.route("/paystack_webhook", methods=["POST", "GET"])
def paystack_webhook():
    try:
        print("✅ Webhook received!")

        if request.method == "GET":
            reference = request.args.get("reference", "No reference provided")
            print(f"🔍 Received GET request. Reference: {reference}")

            payment_verified, amount, status, user_id = verify_paystack_payment(reference)
            print(f"✅ Verification Result: {payment_verified}, {amount}, {status}, {user_id}")

            if payment_verified:
                user_message = f"🎉 *Payment Successful!*\n\n💰 Amount: GHS {amount}\n✅ Status: {status}\n🔗 Reference: `{reference}`"
                send_telegram_message(user_id, user_message)

                telegram_redirect_url = f"https://t.me/drhighspecialBot?start=payment_{reference}"
                return redirect(telegram_redirect_url, code=302)
            else:
                print("❌ Payment verification failed.")
                return "Payment verification failed. Please contact support.", 400

        elif request.method == "POST":
            data = request.get_json()
            if not data:
                print("❌ Received empty POST request!")
                return "Invalid Data", 400

            reference = data["data"].get("reference", "No reference")
            amount = data["data"].get("amount", 0) / 100
            status = data["data"].get("status", "unknown")
            user_id = data["data"]["metadata"].get("user_id", "unknown")

            print(f"🔍 Received POST request. Reference: {reference}, Amount: {amount}, Status: {status}, User ID: {user_id}")

            payment_verified, amount, status, user_id = verify_paystack_payment(reference)
            if payment_verified:
                admin_message = f"🚀 **New Payment Received!**\n\n👤 **User ID:** {user_id}\n💰 **Amount:** GHS {amount}\n✅ **Status:** {status}\n🔗 **Reference:** `{reference}`"
                send_discord_message(admin_message)

                print(f"✅ Payment Processed: {reference} | Amount: {amount} | Status: {status}")
                return "Webhook processed successfully", 200
            else:
                print("❌ Payment verification failed.")
                return "Payment verification failed", 400

    except Exception as e:
        print("❌ ERROR in paystack_webhook():", str(e))
        traceback.print_exc()  # Prints the full error traceback
        return "Internal Server Error", 500

@app.route("/", methods=["GET"])
def home():
    return "Webhook is running!", 200

def send_discord_message(message):
    """Send payment notifications to Discord webhook."""
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

    if not DISCORD_WEBHOOK_URL:
        print("❌ Discord Webhook URL is missing!")
        return False

    data = {"content": message}  # Message to send

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:  # Discord returns 204 No Content on success
            print("✅ Discord message sent successfully!")
            return True
        else:
            print(f"❌ Discord Error: {response.status_code}, {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Discord Request Failed: {e}")
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
