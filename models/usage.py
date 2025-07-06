import mysql.connector
import datetime
import os

# Function to get a connection to Google Cloud SQL
def get_db_connection():
    """
    Establishes a connection to the Google Cloud SQL instance using mysql-connector.
    """
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection

# Function to log usage data
def log_usage(client_id, endpoint, usage_cost):
    """
    Logs usage data for a specific client.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usage_logs (client_id, endpoint, timestamp, usage_cost)
        VALUES (%s, %s, %s, %s)
    """, (client_id, endpoint, datetime.datetime.utcnow(), usage_cost))

    conn.commit()
    cursor.close()
    conn.close()

# Function to get all usage logs for a client
def get_usage_logs(client_id):
    """
    Fetches all usage logs for a specific client.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usage_logs WHERE client_id = %s", (client_id,))
    logs = cursor.fetchall()
    cursor.close()
    conn.close()

    return logs
