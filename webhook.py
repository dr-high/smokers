from flask import Flask, request, jsonify
from database import session, Order
from config import PAYSTACK_SECRET_KEY
import requests

app = Flask(__name__)

PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"

def verify_paystack_payment(reference):
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.get(f"{PAYSTACK_VERIFY_URL}{reference}", headers=headers)
    return response.json()

@app.route('/paystack-webhook', methods=['POST'])
def paystack_webhook():
    payload = request.get_json()

    # Ensure it's a successful payment
    if payload.get('event') == 'charge.success':
        reference = payload['data']['reference']
        user_id = payload['data']['metadata'].get('user_id')
        product_id = payload['data']['metadata'].get('product_id')

        # Verify payment status from Paystack
        verify_response = verify_paystack_payment(reference)

        if verify_response.get('data') and verify_response['data']['status'] == 'success':
            # Update order status
            order = session.query(Order).filter_by(user_id=user_id, product_id=product_id).first()
            if order:
                order.status = 'paid'
                session.commit()
                return jsonify({"status": "success", "message": "Order updated"}), 200
            else:
                return jsonify({"status": "error", "message": "Order not found"}), 404

    return jsonify({"status": "failed", "message": "Invalid event"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
