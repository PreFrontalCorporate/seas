from flask import Blueprint, request, jsonify, current_app
import stripe

# Initialize Stripe API key from Flask app context
def set_stripe_api_key():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    # Ensure the Stripe API key is set in the app context
    set_stripe_api_key()

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    try:
        # Verify the webhook signature and construct event
        event = stripe.Webhook.construct_event(payload, sig_header, current_app.config["STRIPE_WEBHOOK_SECRET"])
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
