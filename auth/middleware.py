# auth/middleware.py

from flask import request, jsonify
from .tokens import verify_token

def token_required(f):
    """
    Decorator that checks if a valid token is included in the request.
    """
    def decorator(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        decoded_token = verify_token(token)
        if not decoded_token:
            return jsonify({"message": "Invalid token!"}), 403

        return f(decoded_token, *args, **kwargs)

    return decorator
