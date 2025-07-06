import os
import stripe
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from auth.middleware import Auth0Middleware
from cvar_app.app.main import cvar_bp
from wasserstein_app.app import wasserstein_bp
from heavy_tail_app.app import heavy_tail_bp
from kolmogorov_app.api.optimize import kolmogorov_bp
from billing.webhooks import webhook_bp
from usage.rate_limiter import rate_limit
from billing.stripe_utils import create_checkout_session, get_plan_details
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

    # Set Flask secret key and other configurations
    app.config['SECRET_KEY'] = os.getenv('FLASK_APP_SECRET_KEY', 'default_secret_key')
    app.config['DEBUG'] = False  # Disable debugging in production
    app.config['ENV'] = 'production'  # Set environment to production
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
    app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET')

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.ejs'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.ejs'), 500

    return app

# Auth0 Middleware Initialization
auth0 = Auth0Middleware(domain="dev-7sz8prkr8rp6t8mx.us.auth0.com", 
                        client_id=os.getenv('AUTH0_CLIENT_ID'), 
                        client_secret=os.getenv('AUTH0_CLIENT_SECRET'))

# Ensure `app` is initialized before defining routes
app = create_master_app()

@app.route('/protected')
@auth0.token_required
def protected_route():
    return {"message": "This is a protected route!"}

@app.route('/login')
def login():
    return redirect(auth0.authorize(callback=url_for('authorized', _external=True)))

@app.route('/login/callback')
def authorized():
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

@app.route('/store')
def store():
    return render_template('store.ejs', plans=get_plan_details())

@app.route('/usage')
@auth0.token_required
def usage(decoded_token):
    client_id = decoded_token['client_id']
    usage_data = get_usage(client_id)  # Fetch from database or external service
    return render_template('usage.ejs', usage=usage_data)

@app.route('/checkout', methods=['POST'])
@auth0.token_required
def checkout(decoded_token):
    client_id = decoded_token['client_id']
    plan = request.json.get('plan')  # E.g., 'cvar_basic'
    session = create_checkout_session(client_id, plan)  # Create session with Stripe
    return jsonify({'checkout_url': session.url})

@app.route("/api/some_endpoint", methods=["POST"])
@auth0.token_required
def some_api_route(decoded_token):
    client_id = decoded_token['client_id']

    if not rate_limit(client_id, max_requests_per_minute=60):
        return {"message": "Rate limit exceeded"}, 429

    return {"message": "Success!"}

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Signature verification failed', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    return '', 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
