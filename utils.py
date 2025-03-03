import phonenumbers, re
from phonenumbers import geocoder, format_number, PhoneNumberFormat
from decimal import Decimal
from getpass import getpass
from argon2 import PasswordHasher
from password_strength import PasswordPolicy, PasswordStats
from rich.console import Console
from rich.prompt import Prompt
from db_conn import get_db_connection

ph = PasswordHasher()
console = Console()

def print_statement(statement, color_tag, bold=False, log=False):
    """Prints a formatted statement with an icon and color based on the tag."""
    color_map = {
        'info': ('cyan', 'ℹ️'),
        'success': ('green', '✅'),
        'warning': ('yellow', '⚠'),
        'danger': ('red', '❌'),
        'notice': ('magenta', '📢'),
        'critical': ('bright_red', '🔥'),
        'debug': ('blue', '🐛')
    }

    color, icon = color_map.get(color_tag, ('white', '❓'))
    formatted_statement = (
        f"[bold {color}]{icon} {statement}[/bold {color}]"
        if bold else f"[{color}]{icon} {statement}[/{color}]"
    )
    
    if log:
        console.log(formatted_statement)
    else:
        console.print(formatted_statement)

def hash_password(password):
    return ph.hash(password)

def unhash_password(password_hash, password):
    try:
        return ph.verify(password_hash, password)
    except:
        return False
    
def is_valid_phone_number(phone_number):
    """Validates an international phone number format."""
    return bool(re.match(r"^\+[1-9]\d{9,14}$", phone_number))

def is_valid_email(email):
    """Validates email format."""
    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return bool(pattern.match(email))


def password_check(phone_number, category='verify'):
    """Verifies the user's password with up to 3 attempts before allowing an action."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE phone_number = %s", (phone_number,))
            user = cur.fetchone()
            if not user:
                print_statement("Incorrect phone number or account does not exist!", "danger", bold=True, log=True)
                return False

    password_hash = user[0]
    attempts = 3
    while attempts > 0:
        console.print("🔑 [bold cyan]Enter Password:[/bold cyan]", end=" ")
        password = getpass("")
        if unhash_password(password_hash, password):
            if category == 'verify':
                print_statement("Password verified successfully!", "success", log=True)
            return True
        attempts -= 1
        print_statement(f"Incorrect password! {attempts} attempt(s) remaining.", "warning")
    if category == 'verify':
        print_statement("Verification failed after 3 incorrect attempts!", "danger", log=True)
    return False

def get_location(phone_number):
    """Formats the phone number and retrieves the location."""
    try:
        parsed_number = phonenumbers.parse(phone_number)
        formatted_number = format_number(parsed_number, PhoneNumberFormat.NATIONAL)
        country = geocoder.description_for_number(parsed_number, 'en')
        formatted_number = f"(+{parsed_number.country_code}) {formatted_number}"
        return formatted_number, country
    except phonenumbers.NumberParseException:
        return "Invalid Number", "Unknown Location"

def get_user_details(phone_number):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username, fullname, phone_number, email, balance, savings_balance FROM users WHERE phone_number = %s", (phone_number,))
            user = cur.fetchone()
            if not user:
                print_statement("Error: Account not found!", "critical")
                return None
            return user

def pass_strength_check(password):
    policy = PasswordPolicy.from_names(
        length=8,    # Minimum length
        uppercase=1, # At least one uppercase letter
        numbers=1,   # At least one digit
        special=1    # At least one special character
    )

    if policy.test(password):
        error = f"Weak password! Doesn't meet requirements: {policy.test(password)}"
        print_statement(error, 'critical')
        validity = False
    else:
        print_statement("Strong password!", 'success')
        validity = True

    # Get password strength score
    stats = PasswordStats(password)
    strength_stat = f"{stats.strength() * 100:.2f}%"
    print_statement(f"Password strength score: {strength_stat}", 'notice')

    return validity

def fetch_users():
    """Fetch all users from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username, fullname, phone_number FROM users ORDER BY fullname ASC")
            return cur.fetchall()

def find_related_usernames(username):
    """Find related usernames based on variations of input."""
    users = fetch_users()
    substrings = {username.replace(" ", "_"), username.replace("_", " "), username.upper(), 
                  username.lower(), username.title(), *username.split(" ")}

    return [user for user in users if user[0] in substrings or any(name in substrings for name in user[1].split(" "))]

def validate_phone_input():
    """Prompt user for a valid phone number."""
    for _ in range(3):
        recipient = Prompt.ask("📞 [bold yellow]Enter recipient's phone number (e.g., +254712345678)[/bold yellow]").strip()
        if is_valid_phone_number(recipient):
            return recipient
        print_statement("Invalid phone number format! Use +[CountryCode][Number] e.g., +254712345678", "critical", bold=True)
    print_statement("Too many failed attempts! Restart the program.", "danger", bold=True, log=True)
    exit()

from rich.prompt import Prompt
from getpass import getpass
import sys

def validate_input(prompt_text, validation_func=None, error_message="Invalid input!", attempts=3, hidden=False):
    """
    Generic function to validate user input.
    
    :param prompt_text: The prompt message for user input
    :param validation_func: A function to validate input (optional)
    :param error_message: The error message to display on invalid input
    :param attempts: Number of allowed attempts before exit
    :param hidden: Whether input should be hidden (for passwords)
    :return: Valid user input
    """
    while attempts > 0:
        user_input = getpass(prompt_text) if hidden else Prompt.ask(prompt_text).strip()

        if not user_input:
            print_statement("Input cannot be empty!", "warning")
        elif validation_func and not validation_func(user_input):
            print_statement(error_message, "critical", bold=True)
        else:
            return user_input  # Return valid input

        attempts -= 1

    print_statement("Too many failed attempts! Restart the program.", "danger", bold=True, log=True)
    sys.exit(1)


def validate_password():
    """
    Function to validate password and confirm password.
    Ensures both passwords match and pass strength requirements.
    """
    attempts = 3
    while attempts > 0:
        password1 = getpass("🔑 [bold cyan]Enter Password:[/bold cyan]").strip()
        password2 = getpass("🔑 [bold magenta]Confirm Password:[/bold magenta]").strip()

        if password1 != password2:
            print_statement("Passwords do not match! Try again.", "warning")
        elif not pass_strength_check(password1):
            print_statement("Password does not meet security requirements!", "critical", bold=True)
        else:
            return password1  # Return valid password

        attempts -= 1

    print_statement("Error: Too many failed attempts! Restart the program.", "danger", bold=True, log=True)
    sys.exit(1)


def fetch_recipient_balance(phone_number):
    """Retrieve recipient balance from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM users WHERE phone_number = %s", (phone_number,))
            result = cur.fetchone()
            return Decimal(result[0]) if result else None

# Enter Username: @John_Doe
# 📛 Enter Full Name: John Doe
# 📞 Enter Phone Number (e.g., +254712345678): +33787654321
# 📧 Enter Email: john_doe@gmail.com