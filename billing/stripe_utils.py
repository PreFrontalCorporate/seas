import stripe
from flask import current_app

def set_stripe_api_key():
    """ Helper function to set the Stripe API key from Flask app context. """
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

def create_checkout_session(price_id, success_url, cancel_url):
    """
    Creates a Stripe checkout session for metered billing.
    """
    # Ensure the Stripe API key is set in the app context
    set_stripe_api_key()

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url
