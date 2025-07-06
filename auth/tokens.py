# auth/tokens.py

import jwt
import datetime
from flask import current_app

def create_token(data, expires_in=3600):
    """
    Creates a JWT token for the client with user-specific data and expiration time.
    """
    payload = {
        **data,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

def verify_token(token):
    """
    Verifies and decodes the JWT token. Returns decoded data if valid, else None.
    """
    try:
        decoded = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
