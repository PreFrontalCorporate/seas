import os
import stripe
from flask import current_app
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Helper function to set the Stripe API key from Flask app context
def set_stripe_api_key():
    """Helper function to set the Stripe API key from Flask app context."""
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

# Function to create a Stripe checkout session
def create_checkout_session(price_id, success_url, cancel_url, user_id):
    """
    Creates a Stripe checkout session for metered billing and stores purchase info in Google Cloud SQL.
    """
    # Ensure the Stripe API key is set in the app context
    set_stripe_api_key()

    # Create the checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    # Save purchase info in Google Cloud SQL
    save_purchase_info(user_id, price_id, session.id)

    return session.url

# Function to save purchase details to Google Cloud SQL
def save_purchase_info(user_id, price_id, session_id):
    """
    Saves purchase information to Google Cloud SQL database.
    """
    # Connect to Google Cloud SQL
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = conn.cursor()

    # Insert the purchase record into the database
    cursor.execute("""
        INSERT INTO purchases (user_id, price_id, session_id, purchase_date)
        VALUES (%s, %s, %s, NOW())
    """, (user_id, price_id, session_id))

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

# Function to get the plan details for rendering in the store page
def get_plan_details():
    """
    Fetches all active plans from the Google Cloud SQL database.
    """
    # Connect to Google Cloud SQL
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = conn.cursor(dictionary=True)

    # Fetch active plans
    cursor.execute("SELECT id, name, price, description, api_price, consulting_rate FROM plans WHERE is_active = 1")
    plans = cursor.fetchall()

    # Close the connection
    cursor.close()
    conn.close()

    return plans
