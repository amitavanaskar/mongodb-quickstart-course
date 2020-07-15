import datetime

import dateutil
from dateutil import parser

from data.bookings import Booking
from data.snakes import Snake
from infrastructure.switchlang import switch
import program_hosts as hosts
import infrastructure.state as state
import services.data_service as svc


def run():
    print(' ****************** Welcome guest **************** ')
    print()

    show_commands()

    while True:
        action = hosts.get_action()

        with switch(action) as s:
            s.case('c', hosts.create_account)  # Create account is already done for hosts. Same utilized.
            s.case('l', hosts.log_into_account)  # Login is already done for hosts. Same utilized.

            s.case('a', add_a_snake)
            s.case('y', view_your_snakes)
            s.case('b', book_a_cage)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')

            s.case('?', show_commands)
            s.case('', lambda: None)
            s.case(['x', 'bye', 'exit', 'exit()'], hosts.exit_app)

            s.default(hosts.unknown_command)

        state.reload_account()

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('[B]ook a cage')
    print('[A]dd a snake')
    print('View [y]our snakes')
    print('[V]iew your bookings')
    print('[M]ain menu')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def add_a_snake():
    print(' ****************** Add a snake **************** ')

    # Done: Require an account
    if not state.active_account:
        hosts.error_msg("You need to login to add a snake.")
        hosts.log_into_account()

    # Done: Get snake info from user
    name = input('What is the name of your snake? ')
    if not name:
        hosts.error_msg('INPUT MISSING - Please input the name of your snake. ')
        add_a_snake()

    species = input('What is the species of your snake? ')
    length = input('What is the length of your snake in meters? ')
    length = length.strip()
    if not length:
        hosts.error_msg('INPUT MISSING - Please enter the length of your snake in meters.')
        add_a_snake()
    try:
        length = float(length)
    except ValueError:
        hosts.error_msg('INPUT ERROR - Please enter a numeric value for snake length in meters [Eg. 1, 2.1, 5, etc].')
        add_a_snake()
    venomous = input('Is your snake venomous [y / n]? ').lower().startswith('y')

    # Done: Create the snake in the DB.
    snake = svc.add_snake(state.active_account, name, species, length, venomous)
    state.reload_account()
    hosts.success_msg(f'Hi {state.active_account.name}, we have added {snake.name} with ID {snake.id}')

    # print(" -------- NOT IMPLEMENTED -------- ")


def view_your_snakes(suppress_header=False):
    if not suppress_header:
        print(' ****************** Your snakes **************** ')

    # Done: Require an account
    if not state.active_account:
        print('You need to login to view your snakes.')
        hosts.log_into_account()

    # Done: Get snakes from DB, show details list
    snakes = svc.find_snakes_for_user(state.active_account)
    print(f'You have {len(snakes)} snake(s) added.')
    if len(snakes) == 0:
        hosts.error_msg("You have not added any snake yet.")
        want_add_snake = input('Do you want to add your snake now [y / n]? ').lower().startswith('y')
        if want_add_snake:
            add_a_snake()
            view_your_snakes()
        return
    for idx, s in enumerate(snakes):
        print(f'    {idx + 1}. {s.name} is a {s.length} meters long {s.species}. Venomous - {s.is_venomous}')

    # print(" -------- NOT IMPLEMENTED -------- ")


def book_a_cage():
    print(' ****************** Book a cage **************** ')

    # Done: Require an account
    if not state.active_account:
        print('You need to login to book a cage.')
        hosts.log_into_account()

    # Done: Verify they have a snake
    snakes = svc.find_snakes_for_user(state.active_account)
    if not snakes:
        hosts.error_msg('You must first add a snake to book a cage.')
        add_a_snake()
        book_a_cage()

    # Done: Select the snake that needs boarding (in case more than 1 snake)
    print("Let's find available cages!")
    view_your_snakes(suppress_header=True)
    if len(snakes) > 1:
        snake_number = input('Select the snake (number) that needs accommodation: ')
        if not snake_number:
            hosts.error_msg('INPUT NEEDED - Please input the snake (number) that needs accommodation [Eg. 1, 2, etc]')
            book_a_cage()
        try:
            snake_number = int(snake_number)
        except ValueError:
            hosts.error_msg('INPUT ERROR - Expected input in numbers [Eg. 1, 2, 3, etc.]')
            book_a_cage()
        selected_snake = svc.find_snakes_for_user(state.active_account)[snake_number - 1]

    else:
        selected_snake = svc.find_snakes_for_user(state.active_account)[0]

    # Done: Get Dates
    start_date_input = input('Enter check-in date [yyyy-mm-dd]: ')
    if not start_date_input:
        hosts.error_msg('INPUT MISSING - Check-in date has not been entered.')
        want_today_checkin = input("Do you want to check for availability today [y / n]? ").lower().startswith('y')
        if want_today_checkin:
            checkin = datetime.datetime.now()
        return
    checkin = parser.parse(start_date_input)

    end_date_input = input('Enter check-out date [yyyy-mm-dd]: ')
    if not end_date_input:
        hosts.error_msg('INPUT MISSING - Check-out date has not been entered.')
        want_oneday_checkout = input("Minimum booking duration is 1 day. \n"
                                     "Do you want to check-out on the same day [y / n]? ").lower().startswith('y')
        if want_oneday_checkout:
            checkout = checkin + datetime.timedelta(days=1)
        return
    checkout = parser.parse(end_date_input)

    if checkout <= checkin:
        hosts.error_msg('INCORRECT INPUT - Check-in date must be before checkout date.')
        book_a_cage()

    # TODO: Check if the snake is booked in any other cage for the duration
    alternate_booking = svc.find_alternate_booking(selected_snake, checkin, checkout)
    if alternate_booking:
        alt_booked_cage = svc.get_cage_for_booking(alternate_booking)
        hosts.error_msg(f'Snake {selected_snake.name} is already booked in cage {alt_booked_cage.name} from '
                        f'{alternate_booking.check_in_date} to {alternate_booking.check_out_date}.\n'
                        f'View your current bookings below -')
        view_bookings()
        input_again = input('Do you want to make another booking [y / n]? ').lower().startswith('y')
        if input_again:
            book_a_cage()
        return

    # Done: Find cages available across date range
    available_cages = svc.get_available_cages(checkin, checkout, selected_snake)

    print(f'There are {len(available_cages)} available cages for {selected_snake.name}.')
    for idx, c in enumerate(available_cages):
        print('    {}. {} of Size {} sq meters. It {} Carpeted, and {} Toys at Price {} / day'.format(
            idx + 1,
            c.name,
            c.square_meters,
            'IS' if c.is_carpeted else 'IS NOT',
            'HAS' if c.has_toys else 'does NOT HAVE',
            c.price
        ))

    if not available_cages:
        print(f'Sorry there are no available cages suitable for {selected_snake.name} for the given dates.')
        try_different_dates = input('Do you wish to modify the search dates [y / n]? ').lower().startswith('y')
        if try_different_dates:
            book_a_cage()
        return

    # Done: Let user select cage to book.
    cage_number = input('Enter the cage (number) you want to book: ')
    if not cage_number:
        hosts.error_msg('INPUT MISSING - You have not entered a cage number.')
        choose_default = input(f'{available_cages[0].name} is a perfect fit. [C]hoose it / [S]earch again / E[x]it. ')\
            .lower()
        if choose_default == 'c':
            cage_number = 1
        elif choose_default == 's':
            book_a_cage()
        return

    try:
        cage_number = int(cage_number)
    except ValueError:
        hosts.error_msg('INCORRECT INPUT - Please input the cage (number) you wish to book [Eg. 1, 2, 3, etc.].')
        book_a_cage()

    selected_cage = available_cages[cage_number - 1]
    svc.book_cage(state.active_account, selected_snake, selected_cage, checkin, checkout)

    hosts.success_msg(f'Successfully booked {selected_cage.name} for {selected_snake.name} at '
                      f'{selected_cage.price}/day')
    # print(" -------- NOT IMPLEMENTED -------- ")


def view_bookings():
    print(' ****************** Your bookings **************** ')
    # Done: Require an account
    if not state.active_account:
        hosts.error_msg('You need to login to view your bookings')
        hosts.log_into_account()

    # Done: List booking info along with snake info
    bookings = svc.get_bookings_for_user(state.active_account)
    print(f'You have {len(bookings)} bookings -')
    for idx, b in enumerate(bookings):
        cage = svc.get_cage_for_booking(b)
        snake = svc.get_snake_for_booking(b)
        print(f" {idx + 1}. Snake {snake.name} is booked at {cage.name} at {b.check_in_date} for "
              f"{(b.check_out_date - b.check_in_date).days} days - "
              f"Price: {(cage.price * ((b.check_out_date - b.check_in_date).days))}")

    # print(" -------- NOT IMPLEMENTED -------- ")
