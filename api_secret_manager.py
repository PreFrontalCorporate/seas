import os
import secrets
import redis
from flask import current_app

# Initialize Redis (reuse your current app settings)
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))

r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

def generate_api_secret(user_id):
    """
    Generate a new unique API secret and store it in Redis under the user ID.
    """
    secret = secrets.token_urlsafe(32)  # 256-bit secure token
    redis_key = f"user:{user_id}:api_secret"
    r.set(redis_key, secret)
    return secret

def get_api_secret(user_id):
    """
    Retrieve an existing API secret for a user.
    """
    redis_key = f"user:{user_id}:api_secret"
    return r.get(redis_key)

def regenerate_api_secret(user_id):
    """
    Regenerate (replace) the API secret for a user.
    """
    return generate_api_secret(user_id)

def validate_api_secret(user_id, provided_secret):
    """
    Validate a given API secret against the stored one for a user.
    """
    stored_secret = get_api_secret(user_id)
    return secrets.compare_digest(stored_secret or '', provided_secret)

