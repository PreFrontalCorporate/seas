import mysql.connector
import time
from flask import current_app

def get_db_connection():
    """
    Establish a connection to Google Cloud SQL database.
    """
    connection = mysql.connector.connect(
        host=current_app.config['DB_HOST'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD'],
        database=current_app.config['DB_NAME']
    )
    return connection

def rate_limit(client_id, max_requests_per_minute):
    """
    Implements a rate limit using Google Cloud SQL to track the number of requests per client.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    current_time = int(time.time())
    time_window = current_time // 60  # Minute granularity
    key = f"rate_limit:{client_id}:{time_window}"

    # Check if the client exceeded the limit
    cursor.execute("""
        SELECT requests FROM client_usage 
        WHERE client_id = %s AND timestamp = %s
    """, (client_id, time_window))
    result = cursor.fetchone()

    if result:
        # Client exists, check requests count
        requests = result[0]
        if requests >= max_requests_per_minute:
            cursor.close()
            connection.close()
            return False  # Limit exceeded

        # Otherwise, increment the requests count
        cursor.execute("""
            UPDATE client_usage 
            SET requests = requests + 1
            WHERE client_id = %s AND timestamp = %s
        """, (client_id, time_window))
    else:
        # No existing record, create a new entry for this client and timestamp
        cursor.execute("""
            INSERT INTO client_usage (client_id, timestamp, requests)
            VALUES (%s, %s, %s)
        """, (client_id, time_window, 1))

    connection.commit()
    cursor.close()
    connection.close()
    return True
