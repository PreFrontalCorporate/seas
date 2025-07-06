import os
import stripe
from flask import Blueprint, request, jsonify, current_app
import mysql.connector

# Initialize Stripe API key from Flask app context
def set_stripe_api_key():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

# Function to get a connection to Google Cloud SQL
def get_db_connection():
    """
    Establishes a connection to the Google Cloud SQL instance using mysql-connector.
    """
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection

# Function to save purchase information to Google Cloud SQL
def save_purchase_info(user_id, price_id, session_id):
    """
    Saves the purchase details to the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO purchases (user_id, price_id, session_id)
        VALUES (%s, %s, %s)
    """, (user_id, price_id, session_id))

    conn.commit()
    cursor.close()
    conn.close()

# Initialize webhook blueprint
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

    # Handle events based on the event type
    if event["type"] == "invoice.payment_succeeded":
        # Update user plan/credits in DB
        session = event["data"]["object"]
        print("Payment succeeded!")
        # Here, you'd extract user ID and plan ID from the session object
        user_id = session["customer"]  # Typically, the customer ID is used
        price_id = session["lines"]["data"][0]["price"]["id"]
        save_purchase_info(user_id, price_id, session["id"])

    elif event["type"] == "customer.subscription.deleted":
        # Deactivate or downgrade the user's subscription
        print("Subscription canceled!")
        session = event["data"]["object"]
        user_id = session["customer"]
        # Perform any necessary updates in the database to reflect the canceled subscription
        save_purchase_info(user_id, "canceled", session["id"])

    return jsonify(success=True)
