import os
import stripe
import redis
import secrets
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, abort
from auth.middleware import Auth0Middleware

# ---- API Blueprints ---------------------------------------------------------
from cvar_app.app.main import cvar_bp
from wasserstein_app.app import wasserstein_bp
from heavy_tail_app.app import heavy_tail_bp
from kolmogorov_app.api.optimize import kolmogorov_bp
from billing.webhooks import webhook_bp

from usage.rate_limiter import rate_limit
from billing.stripe_utils import create_checkout_session, get_plan_details
from dotenv import load_dotenv

# ✨ NEW – Swagger -------------------------------------------------------------
from flasgger import Swagger

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Stripe / Redis config
# -----------------------------------------------------------------------------
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db   = int(os.getenv('REDIS_DB', 0))
r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

# -----------------------------------------------------------------------------
# Auth helper
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# RapidAPI-only auth check
# -----------------------------------------------------------------------------
def verify_api_key_or_abort():
    proxy_secret = request.headers.get('X-RapidAPI-Proxy-Secret')
    if proxy_secret != os.getenv('RAPIDAPI_PROXY_SECRET'):
        abort(401, "Request did not originate from RapidAPI")
    # Remove the key-presence check entirely

# -----------------------------------------------------------------------------
# Inject auth check into every Blueprint BEFORE registration
# -----------------------------------------------------------------------------

@cvar_bp.before_request
@wasserstein_bp.before_request
@heavy_tail_bp.before_request
@kolmogorov_bp.before_request
def _global_api_guard():
    verify_api_key_or_abort()

# -----------------------------------------------------------------------------
# Blueprint‑level documented route example (CVaR)
# -----------------------------------------------------------------------------

@cvar_bp.route("/estimate", methods=["POST"])
def estimate_cvar():
    """
    Estimate CVaR
    ---
    tags:
      - CVaR
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/CVaRRequest'
          examples:
            basic:
              summary: Simple two‑asset portfolio
              value:
                portfolio: [0.3, 0.7]
                confidence_level: 0.95
    responses:
      200:
        description: Result
        content:
          application/json:
            example:
              cvar: -0.0731
              method: historical
    """
    # TODO: Call actual CVaR estimator in cvar_app
    return jsonify({"cvar": -0.0731, "method": "historical"})

# -----------------------------------------------------------------------------
# Wasserstein robust optimiser
# -----------------------------------------------------------------------------

@wasserstein_bp.route("/optimize", methods=["POST"])
def optimize_wasserstein():
    """
    Wasserstein robust portfolio optimisation
    ---
    tags: [Wasserstein]
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              assets:
                type: array
                items: number
              risk_aversion:
                type: number
            required: [assets, risk_aversion]
          example:
            assets: [0.4, 0.6]
            risk_aversion: 0.5
    responses:
      200:
        description: Optimised weights
        content:
          application/json:
            example:
              weights: [0.38, 0.62]
              wasserstein_radius: 0.1
    """
    data = request.get_json(force=True)
    # TODO: Replace with real call e.g., wasserstein_app.app.optimize_portfolio
    weights = [round(x * 0.95, 2) for x in data.get("assets", [])]
    return jsonify({"weights": weights, "wasserstein_radius": 0.1})

# -----------------------------------------------------------------------------
# Heavy-tail volatility simulator
# -----------------------------------------------------------------------------

@heavy_tail_bp.route("/simulate", methods=["POST"])
def simulate_heavy_tail():
    """
    Heavy-tail volatility simulation
    ---
    tags: [HeavyTail]
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              shock_magnitude: {type: number}
              periods: {type: integer}
            required: [shock_magnitude, periods]
          example:
            shock_magnitude: 3.0
            periods: 100
    responses:
      200:
        description: Simulated return series
        content:
          application/json:
            example:
              series: [0.021, -0.033, 0.017]
    """
    data = request.get_json(force=True)
    shock = float(data.get("shock_magnitude", 1))
    periods = int(data.get("periods", 10))
    # Dummy simulation
    series = [round(((i % 2) * -2 + 1) * shock * 0.01, 3) for i in range(periods)]
    return jsonify({"series": series})

# -----------------------------------------------------------------------------
# Kolmogorov complexity explorer
# -----------------------------------------------------------------------------

@kolmogorov_bp.route("/explore", methods=["POST"])
def explore_kolmogorov():
    """
    Kolmogorov complexity explorer
    ---
    tags: [Kolmogorov]
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              data:
                type: array
                items: number
            required: [data]
          example:
            data: [1.2, 0.8, 1.5, 0.6]
    responses:
      200:
        description: Complexity metrics
        content:
          application/json:
            example:
              complexity_score: 0.72
    """
    data = request.get_json(force=True)
    nums = data.get("data", [])
    # Dummy complexity score: normalised variance
    if not nums:
        return jsonify({"complexity_score": 0})
    mean = sum(nums) / len(nums)
    var = sum((x - mean) ** 2 for x in nums) / len(nums)
    complexity = round(min(var / 10, 1), 2)
    return jsonify({"complexity_score": complexity})

# -----------------------------------------------------------------------------
# Factory pattern
# -----------------------------------------------------------------------------

def create_master_app():
    app = Flask(__name__)

    # Register all Blueprints
    app.register_blueprint(cvar_bp,         url_prefix="/cvar")
    app.register_blueprint(wasserstein_bp,  url_prefix="/wasserstein")
    app.register_blueprint(heavy_tail_bp,   url_prefix="/heavy-tail")
    app.register_blueprint(kolmogorov_bp,   url_prefix="/kolmogorov")
    app.register_blueprint(webhook_bp)

    # Core settings
    app.config.update(
        SECRET_KEY           = os.getenv('FLASK_APP_SECRET_KEY', 'default_secret_key'),
        DEBUG                = False,
        ENV                  = 'production',
        STRIPE_SECRET_KEY    = os.getenv('STRIPE_SECRET_KEY'),
        STRIPE_WEBHOOK_SECRET= os.getenv('STRIPE_WEBHOOK_SECRET')
    )

    # Custom error pages
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.ejs'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.ejs'), 500

    return app

# -----------------------------------------------------------------------------
# Build the app & Swagger UI
# -----------------------------------------------------------------------------

auth0 = Auth0Middleware(domain="dev-7sz8prkr8rp6t8mx.us.auth0.com",
                        client_id=os.getenv('AUTH0_CLIENT_ID'),
                        client_secret=os.getenv('AUTH0_CLIENT_SECRET'))

app = create_master_app()

swagger_template = {
    "info": {
        "title": "CBB Homes API",
        "version": "1.0.0",
        "description": "Risk‑analytics & optimisation endpoints for CBB Homes"
    },
    "securityDefinitions": {
        "bearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter **Bearer <YOUR_API_SECRET>**"
        }
    },
    "schemes": ["https"]
}

swagger = Swagger(app, template=swagger_template, merge=True)

# -----------------------------------------------------------------------------
# Helper functions (API secrets, usage, etc.)
# -----------------------------------------------------------------------------
def generate_api_secret(user_id):
    secret = secrets.token_urlsafe(32)
    r.set(f"user:{user_id}:api_secret", secret)
    return secret

def get_api_secret(user_id):
    return r.get(f"user:{user_id}:api_secret")

def regenerate_api_secret(user_id):
    return generate_api_secret(user_id)

def validate_api_secret(user_id, provided):
    stored = get_api_secret(user_id)
    return secrets.compare_digest(stored or '', provided)

# -----------------------------------------------------------------------------
# Auth routes & billing / usage
# -----------------------------------------------------------------------------
@app.route('/protected')
@auth0.token_required
def protected_route():
    return {"message": "This is a protected route!"}

# --------------------------------------------------------------------
# 1. Replace the old /login route with a one‑liner that points to a
#    named helper (“rapidapi_portal”).  This keeps the target URL in
#    one place.
# --------------------------------------------------------------------
@app.route("/login")
def login():
    return redirect(url_for("rapidapi_portal"))

# --------------------------------------------------------------------
# 2. Add *one* helper route that actually points at the public
#    RapidAPI listing.  If you ever change the listing URL you only
#    edit it here.
# --------------------------------------------------------------------
@app.route("/rapidapi")
def rapidapi_portal():
    return redirect(
        "https://rapidapi.com/seas-financial-seas-financial-default/"
        "api/cbb-homes-risk-portfolio-analytics-api"
    )

# --------------------------------------------------------------------
# 3. Catch both Auth0 callback URLs and forward the user to the same
#    RapidAPI page instead of showing an error.  We ignore every
#    query‑string the IdP appends (code, error, state, …).
# --------------------------------------------------------------------
@app.route("/callback")
@app.route("/login/callback")
def auth_callback_passthrough():
    # If Auth0 came back with ?error=… we just swallow it and
    # continue; if it came back with ?code=… we still ignore it
    # because we no longer need the token for interactive pages.
    return redirect(url_for("rapidapi_portal"))

@app.route('/usage')
@auth0.token_required
def usage(decoded_token):
    client_id = decoded_token['client_id']
    usage_data = get_usage(client_id)          # TODO: implement
    secret = get_api_secret(client_id) or generate_api_secret(client_id)
    return render_template('usage.ejs', usage=usage_data, api_secret=secret)

@app.route('/checkout', methods=['POST'])
@auth0.token_required
def checkout(decoded_token):
    client_id = decoded_token['client_id']
    plan     = request.json.get('plan')
    session  = create_checkout_session(client_id, plan)
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
    payload    = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET'))
    except (ValueError, stripe.error.SignatureVerificationError):
        return 'Webhook error', 400
    if event['type'] == 'checkout.session.completed':
        handle_checkout_session(event['data']['object'])   # you must define this util
    return '', 200

@app.route('/')
def index():
    cached = r.get('some_key')
    if not cached:
        cached = 'Hello from Redis!'
        r.set('some_key', cached, ex=300)
    return jsonify(message=cached)

@app.route('/set_cache', methods=['POST'])
def set_cache():
    data = request.json
    r.set(data['key'], data['value'], ex=300)
    return jsonify(message="Data cached successfully")

# --- API secret helper routes -------------------------------------------------
"""
@app.route('/api/generate_secret', methods=['POST'])
@auth0.token_required
def api_generate_secret(decoded_token):
    user_id = decoded_token['client_id']
    return jsonify({"api_secret": generate_api_secret(user_id)})
"""
"""
@app.route('/api/regenerate_secret', methods=['POST'])
@auth0.token_required
def api_regenerate_secret(decoded_token):
    user_id = decoded_token['client_id']
    regenerate_api_secret(user_id)
    return redirect(url_for('usage'))
"""
"""
@app.route('/api/validate_secret', methods=['POST'])
@auth0.token_required
def api_validate_secret(decoded_token):
    user_id = decoded_token['client_id']
    if validate_api_secret(user_id, request.json.get('api_secret')):
        return jsonify({"message": "Secret is valid!"})
    return jsonify({"message": "Invalid secret!"}), 401
"""
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
