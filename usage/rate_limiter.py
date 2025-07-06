import mysql.connector
import time
from flask import current_app

def get_db():
    """
    Connect to the database using configuration from the app.
    """
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['DB_HOST'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME']
        )
    return g.db

def rate_limit(client_id, max_requests_per_minute):
    """
    Implements rate limiting using Google Cloud SQL (MySQL/PostgreSQL).
    Tracks the number of requests per client.
    """
    current_time = int(time.time())
    time_window = current_time // 60  # Minute granularity
    key = f"rate_limit:{client_id}:{time_window}"

    # Get DB connection
    db = get_db()
    cursor = db.cursor()

    # Check if the client has exceeded the limit in the database
    cursor.execute("SELECT count FROM rate_limits WHERE client_id = %s AND time_window = %s", (client_id, time_window))
    row = cursor.fetchone()

    if row:
        requests = row[0]
        if requests >= max_requests_per_minute:
            return False  # Limit exceeded

        # Increment request count
        cursor.execute("UPDATE rate_limits SET count = count + 1 WHERE client_id = %s AND time_window = %s", (client_id, time_window))
    else:
        # Insert a new row if client doesn't exist for this time window
        cursor.execute("INSERT INTO rate_limits (client_id, time_window, count) VALUES (%s, %s, 1)", (client_id, time_window))

    # Commit the transaction
    db.commit()

    return True
