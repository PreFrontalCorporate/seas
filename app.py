import os
import stripe
import redis
import secrets
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

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Redis
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))
r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

# Initialize Flask app
def create_master_app():
    app = Flask(__name__)

    app.register_blueprint(cvar_bp, url_prefix="/cvar")
    app.register_blueprint(wasserstein_bp, url_prefix="/wasserstein")
    app.register_blueprint(heavy_tail_bp, url_prefix="/heavy-tail")
    app.register_blueprint(kolmogorov_bp, url_prefix="/kolmogorov")
    app.register_blueprint(webhook_bp)

    app.config['SECRET_KEY'] = os.getenv('FLASK_APP_SECRET_KEY', 'default_secret_key')
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
    app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET')

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.ejs'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.ejs'), 500

    return app

# Auth0 Middleware
auth0 = Auth0Middleware(domain="dev-7sz8prkr8rp6t8mx.us.auth0.com", 
                        client_id=os.getenv('AUTH0_CLIENT_ID'), 
                        client_secret=os.getenv('AUTH0_CLIENT_SECRET'))

app = create_master_app()

# Utility functions for API secrets
def generate_api_secret(user_id):
    secret = secrets.token_urlsafe(32)
    redis_key = f"user:{user_id}:api_secret"
    r.set(redis_key, secret)
    return secret

def get_api_secret(user_id):
    redis_key = f"user:{user_id}:api_secret"
    return r.get(redis_key)

def regenerate_api_secret(user_id):
    return generate_api_secret(user_id)

def validate_api_secret(user_id, provided_secret):
    stored_secret = get_api_secret(user_id)
    return secrets.compare_digest(stored_secret or '', provided_secret)

# New utility to verify permanent API key in sub-apps
def verify_api_key():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    api_secret = auth_header.split(' ')[1]

    # Check all keys in Redis
    keys = r.keys('user:*:api_secret')
    for key in keys:
        stored = r.get(key)
        if stored == api_secret:
            user_id = key.split(':')[1]
            return user_id
    return None

# Example: protect an endpoint in each blueprint (repeat similar in each sub-app)
@cvar_bp.before_request
def require_api_key_cvar():
    if not verify_api_key():
        return jsonify({"message": "Unauthorized"}), 401

@wasserstein_bp.before_request
def require_api_key_wasserstein():
    if not verify_api_key():
        return jsonify({"message": "Unauthorized"}), 401

@heavy_tail_bp.before_request
def require_api_key_heavy_tail():
    if not verify_api_key():
        return jsonify({"message": "Unauthorized"}), 401

@kolmogorov_bp.before_request
def require_api_key_kolmogorov():
    if not verify_api_key():
        return jsonify({"message": "Unauthorized"}), 401

# Auth routes
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
    usage_data = get_usage(client_id)  # Implement or update this
    secret = get_api_secret(client_id)
    if not secret:
        secret = generate_api_secret(client_id)
    return render_template('usage.ejs', usage=usage_data, api_secret=secret)

@app.route('/checkout', methods=['POST'])
@auth0.token_required
def checkout(decoded_token):
    client_id = decoded_token['client_id']
    plan = request.json.get('plan')
    session = create_checkout_session(client_id, plan)
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
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET'))
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Signature verification failed', 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        handle_checkout_session(session_obj)  # You need to define this

    return '', 200

@app.route('/')
def index():
    cached_value = r.get('some_key')
    if not cached_value:
        cached_value = 'Hello from Redis!'
        r.set('some_key', cached_value, ex=300)
    return jsonify(message=cached_value)

@app.route('/set_cache', methods=['POST'])
def set_cache():
    data = request.json
    r.set(data['key'], data['value'], ex=300)
    return jsonify(message="Data cached successfully")

# === API secret routes ===
@app.route('/api/generate_secret', methods=['POST'])
@auth0.token_required
def api_generate_secret(decoded_token):
    user_id = decoded_token['client_id']
    new_secret = generate_api_secret(user_id)
    return jsonify({"message": "API secret generated.", "api_secret": new_secret})

@app.route('/api/regenerate_secret', methods=['POST'])
@auth0.token_required
def api_regenerate_secret(decoded_token):
    user_id = decoded_token['client_id']
    regenerate_api_secret(user_id)
    return redirect(url_for('usage'))

@app.route('/api/validate_secret', methods=['POST'])
@auth0.token_required
def api_validate_secret(decoded_token):
    user_id = decoded_token['client_id']
    data = request.json
    provided_secret = data.get('api_secret')
    if validate_api_secret(user_id, provided_secret):
        return jsonify({"message": "Secret is valid!"})
    else:
        return jsonify({"message": "Invalid secret!"}), 401

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
