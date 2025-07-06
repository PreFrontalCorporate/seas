import os
import stripe
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from auth.middleware import token_required
from auth.tokens import verify_token
from cvar_app.app.main import cvar_bp
from wasserstein_app.app import wasserstein_bp
from heavy_tail_app.app import heavy_tail_bp
from kolmogorov_app.api.optimize import kolmogorov_bp
from billing.webhooks import webhook_bp
from usage.rate_limiter import rate_limit
from billing.stripe_utils import create_checkout_session, check_payment_status, get_plan_details
from auth0 import Auth0

# Initialize Stripe with the secret key from environment variables
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize the Flask app
def create_master_app():
    app = Flask(__name__)

    # Register blueprints from each sub-API
    app.register_blueprint(cvar_bp, url_prefix="/cvar")
    app.register_blueprint(wasserstein_bp, url_prefix="/wasserstein")
    app.register_blueprint(heavy_tail_bp, url_prefix="/heavy-tail")
    app.register_blueprint(kolmogorov_bp, url_prefix="/kolmogorov")
    app.register_blueprint(webhook_bp)  # For Stripe webhook handling

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.ejs'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.ejs'), 500

    return app

# Auth0 Login route example
@app.route('/login')
def login():
    auth0 = Auth0(domain="dev-7sz8prkr8rp6t8mx.us.auth0.com")
    return redirect(auth0.authorize(callback=url_for('authorized', _external=True)))

@app.route('/login/callback')
def authorized():
    auth0 = Auth0(domain="dev-7sz8prkr8rp6t8mx.us.auth0.com")
    response = auth0.authorized_response()
    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    session['auth_token'] = response['access_token']
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('auth_token', None)
    return redirect(url_for('index'))

# Store Route for Selecting Plans
@app.route('/store')
def store():
    # Show pricing tiers and plans (hardcoded for now)
    return render_template('store.ejs', plans=get_plan_details())

# Usage Route for Monitoring API Usage
@app.route('/usage')
@token_required
def usage(decoded_token):
    # Get usage data based on decoded token (client_id)
    client_id = decoded_token['client_id']
    usage_data = get_usage(client_id)  # Fetch from database or external service
    return render_template('usage.ejs', usage=usage_data)

# Billing Route to handle Stripe Checkout
@app.route('/checkout', methods=['POST'])
@token_required
def checkout(decoded_token):
    client_id = decoded_token['client_id']
    # Get the selected plan from the POST request
    plan = request.json.get('plan')  # E.g., 'cvar_basic'
    session = create_checkout_session(client_id, plan)  # Create session with Stripe
    return jsonify({'checkout_url': session.url})

# Example of an API route with authentication & rate limiting
@app.route("/api/some_endpoint", methods=["POST"])
@token_required
def some_api_route(decoded_token):
    """
    This endpoint requires a valid token and rate-limits the number of requests per minute.
    """
    client_id = decoded_token['client_id']

    if not rate_limit(client_id, max_requests_per_minute=60):
        return {"message": "Rate limit exceeded"}, 429

    # Process the request here
    return {"message": "Success!"}

# Stripe Webhook for Payment Success or Failure
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        # Verify the webhook signature and process event
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )

    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Signature verification failed', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Update user subscription status or whatever you need to do here
        handle_checkout_session(session)

    return '', 200  # Stripe sends no response needed

# Initialize the app and run
if __name__ == "__main__":
    app = create_master_app()
    app.run(debug=True, host="0.0.0.0", port=8080)
