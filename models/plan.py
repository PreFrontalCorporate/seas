import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Function to get all active plans
def get_active_plans():
    """
    Fetches all active plans from the plans table in Google Cloud SQL.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM plans WHERE is_active = 1")
    plans = cursor.fetchall()

    cursor.close()
    conn.close()

    return plans

# Function to get a single plan by ID
def get_plan_by_id(plan_id):
    """
    Fetches a plan by its ID from the plans table in Google Cloud SQL.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM plans WHERE id = %s", (plan_id,))
    plan = cursor.fetchone()

    cursor.close()
    conn.close()

    return plan

# Function to create a new plan
def create_plan(name, price, api_price, consulting_rate, description):
    """
    Creates a new plan in the plans table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO plans (name, price, api_price, consulting_rate, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, price, api_price, consulting_rate, description, True))

    conn.commit()
    cursor.close()
    conn.close()

# Function to update an existing plan
def update_plan(plan_id, name, price, api_price, consulting_rate, description, is_active):
    """
    Updates an existing plan in the plans table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE plans
        SET name = %s, price = %s, api_price = %s, consulting_rate = %s, description = %s, is_active = %s
        WHERE id = %s
    """, (name, price, api_price, consulting_rate, description, is_active, plan_id))

    conn.commit()
    cursor.close()
    conn.close()

# Function to delete a plan
def delete_plan(plan_id):
    """
    Deletes a plan from the plans table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM plans WHERE id = %s", (plan_id,))

    conn.commit()
    cursor.close()
    conn.close()
