import psycopg2, os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("BANK_DB"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

def create_users_table():
    """Creates the users table if it does not exist."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(50) NOT NULL,
                    fullname VARCHAR(100) NOT NULL,
                    phone_number VARCHAR(15) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    balance NUMERIC(12, 2) DEFAULT 0.00,
                    savings_balance NUMERIC(12, 2) DEFAULT 0.00,
                    password_hash TEXT NOT NULL
                );
            """)

            conn.commit()

create_users_table()