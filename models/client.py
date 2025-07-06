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

# Function to create a new client
def create_client(name, email, plan_id, trial_end_date):
    """
    Create a new client record in the 'clients' table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clients (name, email, plan_id, created_at, trial_end_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, email, plan_id, datetime.datetime.utcnow(), trial_end_date))

    conn.commit()
    cursor.close()
    conn.close()

# Function to get client by ID
def get_client_by_id(client_id):
    """
    Get client information by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
    client = cursor.fetchone()
    cursor.close()
    conn.close()

    return client

# Function to update client information
def update_client(client_id, name=None, email=None, plan_id=None, active=None):
    """
    Update client information in the 'clients' table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    update_query = "UPDATE clients SET "
    params = []

    if name:
        update_query += "name = %s, "
        params.append(name)
    if email:
        update_query += "email = %s, "
        params.append(email)
    if plan_id:
        update_query += "plan_id = %s, "
        params.append(plan_id)
    if active is not None:
        update_query += "active = %s, "
        params.append(active)

    # Remove trailing comma and space
    update_query = update_query.rstrip(', ')

    update_query += " WHERE id = %s"
    params.append(client_id)

    cursor.execute(update_query, tuple(params))
    conn.commit()
    cursor.close()
    conn.close()

# Function to deactivate a client
def deactivate_client(client_id):
    """
    Deactivate a client.
    """
    update_client(client_id, active=False)
