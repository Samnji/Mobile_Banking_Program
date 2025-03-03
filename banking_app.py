#!.venv/bin/python3

import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from auth import login, create_account
from transactions import *
from utils import (
    print_statement,
    print_statement, 
    is_valid_phone_number,
    get_user_details,
    get_location
)

console = Console()

BANNER = """ 
[bold cyan]
 __  __       _     _ _        ____              _    _             
|  \/  | ___ | |__ (_) | ___  | __ )  __ _ _ __ | | _(_)_ __   __ _ 
| |\/| |/ _ \| '_ \| | |/ _ \ |  _ \ / _` | '_ \| |/ / | '_ \ / _` |
| |  | | (_) | |_) | | |  __/ | |_) | (_| | | | |   <| | | | | (_| |
|_|  |_|\___/|_.__/|_|_|\___| |____/ \__,_|_| |_|_|\_\_|_| |_|\__, |
                                                              |___/                     
[/bold cyan]
"""

WELCOME_MESSAGES = {
    "login": """[magenta]
🌟 Welcome to the Future of Banking 🌟  

No waits, no lines—just speed and trust. Your wealth is secured, your power just.  
Blockchain shields, smart contracts guide, every transaction clear, nothing to hide.  
No hidden fees, no lost control—just seamless banking, your only goal.  

🚀 Step into the revolution—bank with ease, day and night! 🚀  
[/magenta]
""",
    "signup": """[magenta]
🎉 Welcome to the Future of Banking! 🎉\n\n 
We’re excited to have you on board. Creating an account is simple and secure. 🚀\n 
Just follow the prompts to set up your profile and enjoy seamless banking at your fingertips! 💰🔒
[/magenta]
"""
}

COPYRIGHT = "[bold blue]💡 Crafted by Samuel Njiiri—where innovation meets trust, and code shapes the future. 🚀[/bold blue]"

MENU_OPTIONS = {
    1: ("Deposit Funds", deposit),
    2: ("Withdraw Funds", withdraw),
    3: ("Send Money", send),
    4: ("View Account Statement", view_statement),
    5: ("Save Money", save),
    6: ("Withdraw from Savings", withdraw_from_savings),
    0: ("Exit", exit),
}

def display_welcome():
    """Displays the welcome banner and copyright."""
    console.print(BANNER)
    console.print(COPYRIGHT)

def create_table(data, headers=("Attribute", "Details"), styles=("bold yellow", "bold green")):
    """Creates a styled Rich Table."""
    table = Table(show_header=False, header_style="bold magenta")
    table.add_column(headers[0], style=styles[0], justify="left")
    table.add_column(headers[1], style=styles[1])
    
    for label, value in data:
        table.add_row(label, value)
    
    return table

def main(phone_number):
    """Displays user profile details and presents banking options."""
    
    user_details = get_user_details(phone_number)

    if not user_details:
        print_statement("Error: Unable to fetch user details. Please try again.", "danger")
        return

    console.print(Panel("[bold cyan]🌟 Welcome to Your Banking Dashboard 🌟[/bold cyan]", expand=False))

    # Display user profile
    formatted_number, country = get_location(phone_number)
    profile_data = [
        ("👤 Username", user_details[0]),
        ("📛 Full Name", user_details[1]),
        ("📞 Phone Number", formatted_number),
        ("📍 Location", country),
        ("📧 Email", user_details[3]),
        ("💰 Account Balance", f"$ {user_details[4]:,.2f}"),
        ("💾 Savings Balance", f"$ {user_details[5]:,.2f}"),
    ]
    console.print(create_table(profile_data))

    while True:
        console.print(Panel("[bold cyan]✨ Choose an Action ✨[/bold cyan]", expand=False))

        menu_data = [(f"{key}️⃣", action[0]) for key, action in MENU_OPTIONS.items()]
        console.print(create_table(menu_data, headers=("Option", "Action"), styles=("bold yellow", "bold green")))

        try:
            choice = int(console.input("[bold magenta]💡 Enter your choice: [/bold magenta]"))

            if choice in MENU_OPTIONS:
                action = MENU_OPTIONS[choice][1]
                if action == exit:
                    action()
                else:
                    user_details = get_user_details(phone_number)  # Refresh user details
                    action(user_details)
            else:
                print_statement("Invalid choice! Please select a valid option.", "danger", bold=True)

        except ValueError:
            print_statement("⚠ Invalid input! Please enter a valid number.", "warning", bold=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Usage: ./banking_app.py -n <phone_number> or [-c]")
    parser.add_argument('-n', '--number', type=str, help="Specify a phone number starting with the country code, e.g., +254712345678")
    parser.add_argument('-c', '--create_account', action="store_true", help="Create an account if not registered")

    args = parser.parse_args()

    try:
        if args.create_account and not args.number:
            display_welcome()
            console.print(WELCOME_MESSAGES["signup"])
            create_account()
            exit(0)
    except KeyboardInterrupt:
        print_statement("\nCancelled by the user! Exiting....", "warning", bold=True)
        exit()

    if not args.number and not args.create_account:
        print_statement("Phone number is required! Use -n <phone_number> or -h for help.", "critical", bold=True)
        exit(1)

    if args.number and args.create_account:
        print_statement("You have to provide one flag at a time. Check help using -h flag", "critical", bold=True)
        exit(2)

    phone_number = args.number.strip()

    if not is_valid_phone_number(phone_number):
        print_statement("Invalid phone number format! Use +[CountryCode][Number] e.g., +254712345678", "critical", bold=True)
        exit(1)

    try:
        if login(phone_number):
            display_welcome()
            console.print(WELCOME_MESSAGES["login"])
            main(phone_number)
        else:
            print_statement("Authentication failed. Use -c to create an account if you don't have an account.", "critical", bold=True)
    except KeyboardInterrupt:
        print_statement("\nCancelled by the user! Exiting....", "warning", bold=True)
        main(phone_number)