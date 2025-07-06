# billing/stripe_utils.py

import stripe
from flask import current_app

stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

def create_checkout_session(price_id, success_url, cancel_url):
    """
    Creates a Stripe checkout session for metered billing.
    """
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url
