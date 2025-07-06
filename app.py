from flask import Flask, jsonify, request
from auth.middleware import token_required
from cvar_app.app.main import cvar_bp
from wasserstein_app.app import wasserstein_bp
from heavy_tail_app.app import heavy_tail_bp
from kolmogorov_app.api.optimize import kolmogorov_bp
from billing.webhooks import webhook_bp
from usage.rate_limiter import rate_limit
from auth.tokens import verify_token

# Initialize the Flask app
def create_master_app():
    app = Flask(__name__)

    # Register blueprints from each sub-API
    app.register_blueprint(cvar_bp, url_prefix="/cvar")
    app.register_blueprint(wasserstein_bp, url_prefix="/wasserstein")
    app.register_blueprint(heavy_tail_bp, url_prefix="/heavy-tail")
    app.register_blueprint(kolmogorov_bp, url_prefix="/kolmogorov")
    app.register_blueprint(webhook_bp)  # For Stripe webhook handling

    return app

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

# Initialize the app and run
if __name__ == "__main__":
    app = create_master_app()
    app.run(debug=True, host="0.0.0.0", port=8080)
