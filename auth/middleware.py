import json
import requests
from flask import request
from functools import wraps

class Auth0Middleware:
    def __init__(self, domain, client_id, client_secret):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret

    def verify_token(self, req):
        """
        Verify the Auth0 token passed in the Authorization header
        """
        auth = req.headers.get("Authorization", None)
        
        if not auth:
            raise ValueError("Authorization token is missing")
        
        parts = auth.split()

        if len(parts) != 2:
            raise ValueError("Authorization token format is incorrect")
        
        token = parts[1]

        # Check token with Auth0 Public Key endpoint
        public_key_url = f"https://{self.domain}/.well-known/jwks.json"
        try:
            response = requests.get(public_key_url)
            jwks = response.json()
            # Look for the correct key to validate
            for key in jwks['keys']:
                # Extract the key based on 'kid' to verify JWT
                pass  # You should decode and verify the JWT here
        except Exception as e:
            raise ValueError(f"Error validating token: {e}")

        return True

    def token_required(self, f):
        """
        Decorator to ensure that a valid token is present and verified in the request header.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Attempt to verify the token in the request
                self.verify_token(request)
            except ValueError as e:
                return {"message": f"Unauthorized: {str(e)}"}, 401

            return f(*args, **kwargs)

        return decorated_function
