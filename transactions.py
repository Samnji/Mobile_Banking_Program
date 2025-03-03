import logging
from decimal import Decimal, InvalidOperation
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from db_conn import get_db_connection
from blockchain import Blockchain, Transaction
from utils import (
    print_statement, 
    validate_phone_input,
    fetch_recipient_balance,
    find_related_usernames,
    password_check
)

# Configure logging
logging.basicConfig(filename="transactions.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

console = Console()
TRANSACTION_COST = {
    "send": 0.009,
    "withdrawal": 0.015,
}

# Initialize blockchain
blockchain = Blockchain()

def validate_amount_input(category):
    """Prompt user for a valid transaction amount."""
    try:
        amount = Decimal(Prompt.ask(f"💸 [bold cyan]Enter the amount to {category} in Dollars($) [/bold cyan]"))
        if amount > 0:
            return amount
        print_statement("Amount must be greater than zero!", "warning")
    except InvalidOperation:
        print_statement("Invalid amount! Please enter a valid number.", "danger")
        logging.error("Invalid amount input for transaction.")
    return None

def record_transaction(sender, recipient, amount, transaction_type):
    """Adds a new transaction to the blockchain."""
    tx = Transaction(sender, recipient, float(amount), transaction_type)
    blockchain.add_transaction(tx)
    blockchain.mine_block()
    logging.info(f"Blockchain updated: {transaction_type} of ${amount:.2f} from {sender} to {recipient}.")

def deposit(user_details):
    """Deposits an amount into the user's account."""
    fullname, phone_number, balance = user_details[1], user_details[2], Decimal(user_details[4])
    amount = validate_amount_input("deposit")
    if not amount:
        return

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            new_balance = balance + amount
            cur.execute("UPDATE users SET balance = %s WHERE phone_number = %s", (new_balance, phone_number))
            conn.commit()
            
            # Record transaction in blockchain
            record_transaction("SYSTEM", phone_number, amount, "DEPOSIT")

            logging.info(f"Deposit: {phone_number} deposited ${amount:.2f}. New balance: ${new_balance:.2f}")
            print_statement(
                f"Dear {fullname}, you have successfully deposited ${amount}.",
                "success",
            )


def withdraw(user_details):
    """Handles withdrawal after verifying the user's password."""
    fullname, phone_number, balance = user_details[1], user_details[2], Decimal(user_details[4])
    amount = validate_amount_input("withdraw")
    if not amount:
        return

    transaction_fee = amount * Decimal(TRANSACTION_COST["withdrawal"])
    total_amount = transaction_fee + amount

    if total_amount > balance:
        print_statement("Insufficient funds!", "warning")
        return

    if not password_check(phone_number):
        print_statement("Withdrawal canceled due to failed verification.", "danger", bold=True)
        return

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            new_balance = balance - total_amount
            cur.execute("UPDATE users SET balance = %s WHERE phone_number = %s", (new_balance, phone_number))
            conn.commit()
            
            # Record transaction in blockchain
            record_transaction(phone_number, "ATM", amount, "WITHDRAWAL")

            logging.info(f"Withdrawal: {phone_number} withdrew ${amount:.2f}. New balance: ${new_balance:.2f}")
            print_statement(
                f"Dear {fullname}, you have successfully withdrawn ${amount}.",
                "success",
            )

def send(user_details):
    """Handles money transfer between users."""
    fullname, phone_number, balance = user_details[1], user_details[2], Decimal(user_details[4])

    for _ in range(3):
        search_by = Prompt.ask("🔍 [bold green]Search recipient by \[n for name] or \[p for phone number]?[/bold green]").strip().lower()

        if search_by == "n":
            name = Prompt.ask("👤 [bold cyan]Enter name[/bold cyan]").strip()
            if not name:
                print_statement("name cannot be empty!", "warning")
                continue

            matching_users = find_related_usernames(name)
            if not matching_users:
                console.print("[bold red]No users found![/bold red]")
                continue

            # Display matching users
            table = Table(title="📋 User Accounts", title_style="bold cyan")
            table.add_column("Username", justify="center", style="bold green")
            table.add_column("Full Name", justify="center", style="bold magenta")
            table.add_column("Phone Number", justify="center", style="bold blue")

            for user in matching_users:
                table.add_row(user[0], user[1], user[2])

            console.print(table)
            console.print("📋 [bold cyan]Copy the phone number of the recipient you wish to send money to from the list above.[/bold cyan]")

            recipient = validate_phone_input()

        elif search_by == "p":
            recipient = validate_phone_input()
        
        else:
            print_statement("Invalid input! Please enter \[n for name] or \[p for phone number].", "danger")
            continue
        recipient_balance = fetch_recipient_balance(recipient)
        if recipient_balance is None:
            print_statement("Recipient not found!", "danger")
            continue
        break
    else:
        print_statement("Too many failed attempts! Restart the program.", "danger", bold=True, log=True)
        return
    recipient_balance = fetch_recipient_balance(recipient)
    if recipient_balance is None or recipient == phone_number:
        print_statement("Invalid recipient!", "danger")
        return
    
    amount = validate_amount_input("send")
    if not amount:
        return

    transaction_fee = amount * Decimal(TRANSACTION_COST["send"])
    total_amount = transaction_fee + amount

    if total_amount > balance:
        print_statement("Insufficient balance!", "warning")
        return

    if not password_check(phone_number):
        print_statement("Transaction canceled due to failed verification.", "danger")
        return

    new_balance_sender = balance - total_amount
    new_balance_recipient = recipient_balance + amount

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET balance = %s WHERE phone_number = %s", (new_balance_sender, phone_number))
            cur.execute("UPDATE users SET balance = %s WHERE phone_number = %s", (new_balance_recipient, recipient))
            conn.commit()
            
            # Record transaction in blockchain
            record_transaction(phone_number, recipient, amount, "TRANSFER")

    logging.info(f"Send money: {phone_number} sent ${amount:.2f} to {recipient}.")
    print_statement(
        f"Dear {fullname}, you have successfully sent ${amount} to {recipient}.",
        "success",
    )

def view_statement(user_details):
    """Displays the user's current balance after authentication and logs access."""
    phone_number, balance = user_details[2], Decimal(user_details[4])
    print_statement(f"📜 Your balance is: ${balance:,.2f}", "info")
    logging.info(f"Balance inquiry: {phone_number} checked balance. Balance: ${balance:.2f}")

def save(user_details):
    """Handles saving money into the savings account."""
    fullname, phone_number, balance = user_details[1], user_details[2], Decimal(user_details[4])
    amount = validate_amount_input("save")
    if not amount or amount > balance:
        print_statement("Insufficient funds!", "warning")
        logging.warning(f"Savings deposit failed: Insufficient funds for {phone_number}.")
        return

    if not password_check(phone_number):
        print_statement("Saving canceled due to failed verification.", "danger", bold=True)
        logging.warning(f"Savings deposit failed: Incorrect password for {phone_number}.")
        return

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT savings_balance FROM users WHERE phone_number = %s", (phone_number,))
            savings_balance = cur.fetchone()[0]
            new_balance = balance - amount
            new_savings_balance = savings_balance + amount
            cur.execute("UPDATE users SET balance = %s WHERE phone_number = %s", (new_balance, phone_number))
            cur.execute("UPDATE users SET savings_balance = %s WHERE phone_number = %s", (new_savings_balance, phone_number))
            conn.commit()

    logging.info(f"Savings deposit: {phone_number} saved ${amount:.2f}. New balance: ${new_balance:.2f}, Savings balance: ${new_savings_balance:.2f}")
    print_statement(
        f"Dear {fullname}, you have successfully added ${amount:,.2f} to your savings!\n"
        f"   New account balance: ${new_balance:,.2f}\n"
        f"   New savings balance: ${new_savings_balance:,.2f}",
        "success",
    )


def withdraw_from_savings(user_details):
    """Handles withdrawal after verifying the user's password."""
    fullname, phone_number, balance = user_details[1], user_details[2], Decimal(user_details[4])
    
    logging.info(f"User {fullname} ({phone_number}) initiated a withdrawal from savings.")

    # Get and validate transfer amount
    amount = validate_amount_input("withdraw from savings")
    if not amount:
        logging.warning(f"User {fullname} ({phone_number}) entered an invalid amount.")
        return
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT savings_balance FROM users WHERE phone_number = %s", (phone_number,))
            savings_balance = cur.fetchone()[0]
            
            if amount > savings_balance:
                logging.warning(f"User {fullname} ({phone_number}) has insufficient savings balance.")
                print_statement("Insufficient funds!", "warning")
                return
            
            if not password_check(phone_number):
                logging.warning(f"User {fullname} ({phone_number}) failed password verification for withdrawal.")
                print_statement("Withdraw from savings canceled due to failed verification.", "danger", bold=True)
                return
            
            new_balance = balance + amount
            new_savings_balance = savings_balance - amount
            cur.execute("UPDATE users SET balance = %s WHERE phone_number = %s", (new_balance, phone_number))
            cur.execute("UPDATE users SET savings_balance = %s WHERE phone_number = %s", (new_savings_balance, phone_number))
            conn.commit()
            
            logging.info(f"User {fullname} ({phone_number}) successfully withdrew ${amount:,.2f} from savings. "
                         f"New balance: ${new_balance:,.2f}, New savings: ${new_savings_balance:,.2f}")
            
            print_statement(
                f"Dear {fullname}, you have successfully withdrawn ${amount:,.2f} from your savings!\n"
                f"   New account balance: ${new_balance:,.2f}\n"
                f"   New savings balance: ${new_savings_balance:,.2f}",
                "success",
            )
