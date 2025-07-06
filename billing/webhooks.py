# billing/webhooks.py

from flask import Blueprint, request, jsonify
import stripe

stripe.api_key = "your_stripe_secret_key"
endpoint_secret = "your_webhook_secret"

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    # Handle events
    if event["type"] == "invoice.payment_succeeded":
        # Update user plan/credits in DB
        print("Payment succeeded!")
    elif event["type"] == "customer.subscription.deleted":
        # Deactivate or downgrade the user's subscription
        print("Subscription canceled!")

    return jsonify(success=True)
