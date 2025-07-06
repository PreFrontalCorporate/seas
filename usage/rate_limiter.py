# usage/rate_limiter.py

import redis
import time
from flask import current_app

r = redis.Redis(host=current_app.config['REDIS_HOST'], port=current_app.config['REDIS_PORT'], db=0)

def rate_limit(client_id, max_requests_per_minute):
    """
    Implements a rate limit using Redis to track the number of requests per client.
    """
    key = f"rate_limit:{client_id}"
    current_time = int(time.time())
    time_window = current_time // 60  # Minute granularity

    # Check if the client exceeded the limit
    requests = r.get(f"{key}:{time_window}")
    if requests and int(requests) >= max_requests_per_minute:
        return False  # Limit exceeded

    # If within limits, increment and return True
    r.incr(f"{key}:{time_window}")
    return True
