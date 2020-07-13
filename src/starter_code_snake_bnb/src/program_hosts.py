import datetime

from colorama import Fore
from dateutil import parser

from infrastructure.switchlang import switch
import infrastructure.state as state
import services.data_service as svc


def run():
    print(' ****************** Welcome host **************** ')
    print()

    show_commands()

    while True:
        action = get_action()

        with switch(action) as s:
            s.case('c', create_account)
            s.case('a', log_into_account)
            s.case('l', list_cages)
            s.case('r', register_cage)
            s.case('u', update_availability)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case(['x', 'bye', 'exit', 'exit()'], exit_app)
            s.case('?', show_commands)
            s.case('', lambda: None)
            s.default(unknown_command)

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('Login to your [a]ccount')
    print('[L]ist your cages')
    print('[R]egister a cage')
    print('[U]pdate cage availability')
    print('[V]iew your bookings')
    print('Change [M]ode (guest or host)')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def create_account():
    print(' ****************** REGISTER **************** ')

    # Done: Get name & email
    name = input('What is your name? ')
    email = input('What is your preferred email? ').strip().lower()  # Remove spaces, all lower case
    """
    In a real website a username password would be needed to create account.
    We could add the mongoengine code to insert these values to the db here. However, it is better to collect all these 
    in a central location that can be used across the application.
    NoSQL or document databases do not have inherent structure to them. Some structure can be add structure by having 
    classes for the data (already done in data folder), and by also having a centralized data access piece.
    """
    # First check that the account does not exist - If not, create account
    old_account = svc.find_account_by_email(email)

    if old_account:
        error_msg(f"ERROR: Account with email {email} already exists.")
        if name.lower() == old_account.name.lower():    # If input name matches existing account name, login
            state.active_account = old_account
            success_msg(f"Hi {state.active_account.name}! You are logged in successfully with email : {email}")
        else:
            return
    else:   # Done : Create account, set as logged in.
        state.active_account = svc.create_account(name, email)
        success_msg(f"Created new account for {name} and {email} with id {state.active_account.id}.")

    """
    Create an account by passing in name and email. This is gives us an account.
    We would want to store that in the statefulness of our application (active). In a web app this is done by cookies. 
    Here this is implemented through state active account.
    Pycharm tip - Alt + Enter to create the missing function.
    """


def log_into_account():
    print(' ****************** LOGIN **************** ')

    # Done: Get email
    email = input("Enter your registered Email: ").strip().lower()  # Remove spaces, all lower case

    # Done : Find account in DB, set as logged in.
    # Check if account exists
    account = svc.find_account_by_email(email=email)

    if not account:
        print(f"Could not find account with email : {email}.")
        want_create_account = input('Do you wish to register an account [y / n]? ').lower().startswith('y')
        if want_create_account:
            create_account()
        return

    # If exists set to active state
    state.active_account = account
    success_msg(f"Hi {state.active_account.name}! You are logged in successfully with email : {email}")

    # print(" -------- NOT IMPLEMENTED -------- ")


def register_cage():
    print(' ****************** REGISTER CAGE **************** ')

    # Done: Require an account
    # Cage needs to be tied to an account, ie, the user registering cage must be logged in
    if not state.active_account:
        error_msg("LOGIN NEEDED - You need to be logged in to register a cage")
        log_into_account()

    # Done: Get info about cage
    sq_meters = input('Specify sie of the cage in square meters: ')
    if not sq_meters:
        error_msg("INPUT REQUIRED - Cage size is missing.")
        return
    try:
        sq_meters = float(sq_meters)
    except ValueError:
        error_msg(f"INPUT ERROR - Please input a numeric value for cage size. Your input - {sq_meters}")

    carpeted = input("Is the cage carpeted [y / n]? ").lower().startswith('y')
    has_toys = input("Have snake toys [y / n]? ").lower().startswith('y')
    allow_dangerous = input("Can you host venomous snakes [y / n]? ").lower().startswith('y')
    price = input("Price of the cage per day: ")
    if not price:
        error_msg("INPUT REQUIRED - Price input is missing.")
        return
    try:
        price = float(price)
    except ValueError:
        error_msg(f"INPUT ERROR - Please input a numeric value for daily price. Your input - {price}")
    name = input("Give your cage a name: ")

    # Done: Save cage to DB.
    cage = svc.register_cage(
        state.active_account, sq_meters, carpeted, has_toys, allow_dangerous, price, name
    )

    state.reload_account()  # To reflect the changes in active account
    success_msg(f"Cage {cage.name} has been registered with ID {cage.id}. Verify Details -\n"
                f"Size - {cage.square_meters}\n"
                f"Price - {price}\n"
                f"Carpeted - {cage.is_carpeted}\n"
                f"Has Toys - {cage.has_toys}\n"
                f"Allow Dangerous Snakes - {cage.allow_dangerous_snakes}")
    # print(" -------- NOT IMPLEMENTED -------- ")


def list_cages(suppress_header=False):
    if not suppress_header:
        print(' ******************     Your cages     **************** ')

    # Done: Require an account
    if not state.active_account:
        error_msg("LOGIN NEEDED - You need to be logged in to register a cage")
        log_into_account()

    # Done: Get cages, list details
    cages = svc.find_cages_for_user(state.active_account)
    print(f'You have {len(cages)} cage(s)')

    # Register cage if no cage?
    if len(cages) == 0:
        want_register_snake = input('Do you want to register a cage [y / n]? ').lower().startswith('y')
        if want_register_snake:
            register_cage()
            list_cages()
        return
    # List out cages
    for idx, c in enumerate(cages):     # Enumerate for easy selection to update availability
        print(f' {idx + 1}. {c.name} is {c.square_meters} square meters')
        for b in c.bookings:
            print('    * Booking Availability: {}, {} Days, Booked? {}'.format(
                b.check_in_date,
                (b.check_out_date - b.check_in_date).days,
                'Yes' if b.booked_date is not None else 'No'
            ))
    # print(" -------- NOT IMPLEMENTED -------- ")


def update_availability():
    print(' ****************** Add available date **************** ')

    # Done: Require an account
    if not state.active_account:
        error_msg('You need to be logged in to update your cage availability.')
        log_into_account()

    # Done: list cages
    list_cages(suppress_header=True)

    # Done: Choose cage
    cage_number = input('Input cage number you want to update availability: ')
    if not cage_number:
        error_msg('INPUT NEEDED - Please input the cage number you want to update. Received no input')
        update_availability()
    try:
        cage_number = int(cage_number.strip().replace('.', ''))
    except ValueError:
        error_msg(f'INCORRECT INPUT - Please input the number of the cage you want to update. \n'
                  f'Received input: {cage_number}')
        update_availability()

    cages = svc.find_cages_for_user(state.active_account)
    selected_cage = cages[cage_number - 1]  # Convert user input back to zero base
    success_msg(f'Selected cage {selected_cage.name}')

    # Done: Set dates, save to DB.
    start_date = parser.parse(
        input(f'Enter available dates of {selected_cage.name} [yyyy-mm-dd]: ')
    )
    days = input(f'For how many days is {selected_cage.name} available? ')
    if not days:
        error_msg(f"INPUT MISSING - Number of days {selected_cage.name} is available is missing.")
        book_month = input(f"    > Max Duration possible by default is a month\n"
                           f"    > Do you want to mark {selected_cage.name} available for a month [y / n]? ").\
            lower().startswith('y')
        if book_month:
            success_msg(f"{selected_cage.name} will be available for 30 days.")
            days = 30
        else:
            error_msg(f"Availability update for {selected_cage.name} cancelled.")
            return
    try:
        days = int(days)
    except ValueError:
        error_msg('INCORRECT INPUT - Please input number of days [Eg. 1, 2, 3, etc]')
        update_availability()

    svc.add_available_date(
        selected_cage, start_date, days
    )

    success_msg(f"Availability dates added for {selected_cage.name}\n"
                f"{selected_cage.name} available from {start_date} to {start_date + datetime.timedelta(days=days)}")
    # print(" -------- NOT IMPLEMENTED -------- ")


def view_bookings():
    print(' ****************** Your bookings **************** ')

    # TODO: Require an account
    # TODO: Get cages, and nested bookings as flat list
    # TODO: Print details for each

    print(" -------- NOT IMPLEMENTED -------- ")


def exit_app():
    print()
    print('bye')
    raise KeyboardInterrupt()


def get_action():
    text = '> '
    if state.active_account:
        text = f'{state.active_account.name}> '

    action = input(Fore.YELLOW + text + Fore.WHITE)
    return action.strip().lower()


def unknown_command():
    print("Sorry we didn't understand that command.")


def success_msg(text):
    print(Fore.LIGHTGREEN_EX + text + Fore.WHITE)


def error_msg(text):
    print(Fore.LIGHTRED_EX + text + Fore.WHITE)
