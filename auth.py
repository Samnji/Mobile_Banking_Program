import sys
import psycopg2
from rich.prompt import Prompt
from rich.console import Console
from db_conn import get_db_connection
from utils import (
    print_statement, 
    is_valid_phone_number, 
    is_valid_email, 
    validate_input,
    validate_password,
    password_check, 
    hash_password, 
    get_db_connection
)

console = Console()

def create_account():
    """Creates a new user account securely with validation."""
    username = validate_input("👤 [bold cyan]Enter Username[/bold cyan]")

    fullname = Prompt.ask("📛 [bold magenta]Enter Full Name[/bold magenta]").strip()

    phone_number = validate_input(
        "📞 [bold yellow]Enter Phone Number (e.g., +254712345678)[/bold yellow]", 
        validation_func=is_valid_phone_number,
        error_message="Invalid phone number format! Use +[CountryCode][Number] e.g., +254712345678"
    )

    email = validate_input(
        "📧 [bold green]Enter Email[/bold green]", 
        validation_func=is_valid_email,
        error_message="Invalid email format!"
    )

    password = validate_password()
    password_hash = hash_password(password)

    # 🔹 Database Insertion
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if phone number or email already exists
                cur.execute("""
                    SELECT user_id FROM users WHERE phone_number = %s OR email = %s
                """, (phone_number, email))
                
                if cur.fetchone():
                    print_statement("Error: Phone number or email already exists!", "danger", log=True)
                    sys.exit(1)

                # Insert new user
                cur.execute("""
                    INSERT INTO users (username, fullname, phone_number, email, password_hash)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, fullname, phone_number, email, password_hash))
                conn.commit()
                
                print_statement(f"Dear {fullname}, your account has been created successfully!", "success", log=True)

    except psycopg2.IntegrityError:
        print_statement("Error: Phone number or email already exists!", "danger", log=True)
        sys.exit(1)
    except Exception as e:
        print_statement(f"Unexpected error: {str(e)}", "danger", log=True)
        sys.exit(1)

def login(phone_number):
    """Logs in a user securely by verifying the password."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT fullname FROM users WHERE phone_number = %s", (phone_number,))
            user = cur.fetchone()

            if not user:
                print_statement("Incorrect phone number or account does not exist!", "danger", bold=True, log=True)
                return False  # No account found
    
    # Check password before allowing login
    if password_check(phone_number, category='login'):
        print_statement(f"Welcome back, {user[0]}!", "success", log=True)
        return True  # Login successful
    else:
        print_statement("Login failed due to incorrect password.", "danger", log=True)
        return False  # Failed login