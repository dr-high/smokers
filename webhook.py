import os
import json
from flask import Flask, request, redirect
import requests
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Details
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")  # Second bot for admin notifications
ADMIN_CHAT_ID = "6009484587"  # Replace with your actual Telegram ID

# Flask App
app = Flask(__name__)

# Paystack Secret Key (for verifying transactions)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# Webhook Route
@app.route("/paystack_webhook", methods=["POST", "GET"])
def paystack_webhook():
    if request.method == "GET":
        # Paystack redirects user after payment
        reference = request.args.get("reference", "No reference provided")

        # ✅ Step 1: Verify Payment Before Redirecting
        payment_verified, amount, status, user_id = verify_paystack_payment(reference)

        if payment_verified:
            # ✅ Step 2: Notify the user about successful payment
            user_message = f"🎉 *Payment Successful!*\n\n💰 Amount: GHS {amount}\n✅ Status: {status}\n🔗 Reference: `{reference}`"
            send_telegram_message(user_id, user_message)

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

        # ✅ Verify Payment Before Notifying Admin
        payment_verified, amount, status, user_id = verify_paystack_payment(reference)

        if payment_verified:
    # ✅ Notify Admin using Discord Webhook
    admin_message = "🚀 **New Payment Received!**\n\n👤 **User ID:** {}\n💰 **Amount:** GHS {}\n✅ **Status:** {}\n🔗 **Reference:** `{}`".format(user_id, amount, status, reference)
    send_discord_message(admin_message)  # Ensure this function exists and is properly defined

    # ✅ Log Event
    print(f"✅ Payment Processed: {reference} | Amount: {amount} | Status: {status}")

    return "Webhook processed successfully", 200

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
