# seas/app.py

from flask import Flask

# Import blueprints from each sub-API
from cvar_app.app.main import cvar_bp
from wasserstein_app.app import wasserstein_bp
from heavy_tail_app.app import heavy_tail_bp
from kolmogorov_app.api.optimize import kolmogorov_bp

def create_master_app():
    app = Flask(__name__)

    # Register each sub-API under a prefix
    app.register_blueprint(cvar_bp, url_prefix="/cvar")
    app.register_blueprint(wasserstein_bp, url_prefix="/wasserstein")
    app.register_blueprint(heavy_tail_bp, url_prefix="/heavy-tail")
    app.register_blueprint(kolmogorov_bp, url_prefix="/kolmogorov")

    return app

if __name__ == "__main__":
    app = create_master_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
