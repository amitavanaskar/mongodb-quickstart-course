import datetime
from typing import List

from data import bookings
from data.bookings import Booking
from data.cages import Cage
from data.owners import Owner
from data.snakes import Snake


def create_account(name: str, email: str) -> Owner:  # Outputs an owner
    owner = Owner()
    owner.name = name
    owner.email = email

    owner.save()
    # When we call save all the default values are set. Primary key (owner.id in python level, owner_id at database
    # level) is automatically generated
    return owner


def find_account_by_email(email: str) -> Owner:
    # owner = Owner.objects().filter(email=email).first()
    # When there is only a single filter statement, code can be shortened
    owner = Owner.objects(email=email).first()
    return owner


def register_cage(
        active_account: Owner, sq_meters: float, carpeted: bool, has_toys: bool, allow_dangerous: bool, price: float,
        name: str
) -> Cage:
    cage = Cage()

    cage.name = name
    cage.price = price
    cage.square_meters = sq_meters
    cage.is_carpeted = carpeted
    cage.has_toys = has_toys
    cage.allow_dangerous_snakes = allow_dangerous

    cage.save()

    # Add relationship with Owner
    account = find_account_by_email(active_account.email)  # Ensures no stale data (Instead of using account directly)
    account.cage_ids.append(cage.id)  # Called save earlier ensures that the cage id is generated
    account.save()  # Pushing the changes we have made to the account to the db

    return cage


def find_cages_for_user(account: Owner) -> List[Cage]:  # Pycharm Tip: Alt + Enter > Typing module choose list
    query = Cage.objects(id__in=account.cage_ids)  # __ is used in mongoengine to leverage mondodb's $ operators
    # Here it will retrieve Cage objects where the cage id is owner's cage_id list
    cages = list(query)  # Executing the query and snapshot it for the app
    return cages


def add_available_date(cage: Cage, start_date: datetime.datetime, days: int) -> Cage:
    booking = Booking()
    booking.check_in_date = start_date
    booking.check_out_date = start_date + datetime.timedelta(days=days)

    cage = Cage.objects(id=cage.id).first()
    cage.bookings.append(booking)  # Bookings are not top level items. They are present inside cages
    cage.save()  # Save cages

    return cage


def add_snake(account: Owner, name: str, species: str, length: float, venomous: bool) -> Snake:
    snake = Snake()
    snake.name = name
    snake.species = species
    snake.length = length
    snake.is_venomous = venomous

    snake.save()

    # Add relationship with owner
    account = find_account_by_email(account.email)
    account.snake_ids.append(snake.id)
    account.save()

    return snake


def find_snakes_for_user(account: Owner) -> List[Snake]:
    account = find_account_by_email(account.email)
    query = Snake.objects(id__in=account.snake_ids)
    snakes = list(query)
    return list(snakes)


def get_available_cages(checkin: datetime.datetime, checkout: datetime.datetime, snake: Snake) -> List[Cage]:
    # TODO: Minimum size of cage is snake length / 4
    # TODO: Find all the cages that have bookings but are not booked in the specified time block
    # TODO: If venomous, only allowed. If not, all
    # snake = Snake.objects(id=snake)
    min_size = snake.length / 4
    query = Cage.objects() \
        .filter(square_meters__gte=min_size) \
        .filter(bookings__check_in_date__lte=checkin) \
        .filter(bookings__check_out_date__gte=checkout)
    # Issue in the above query. Mongoengine does not by default do an element match. As in it does not check that the
    # same booking availability has both available checkin date before the checkin date and available booking checkout
    # date after the checkout date. This is possible to do in PyMongo with $elematch (element match). Therefore the
    # output needs to be filtered again for both conditions. Done in final_cages

    if snake.is_venomous:
        query = query.filter(allow_dangerous_snakes=True)

    cages = query.order_by('price', '-square_meters')  # Show cages first ordered by price, and then ordered by size.
    # ie, for the same price, order cages by size.

    final_cages = []
    c: Cage
    for c in cages:
        b: Booking
        for b in c.bookings:
            if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id is None:
                final_cages.append(c)

    return final_cages


def book_cage(account: Owner, snake: Snake, cage: Cage, checkin: datetime.datetime, checkout: datetime.datetime):
    # Done: Update booking availability - Split.
    #  Available checkin to Booked Checkin,
    #  Booked Checkin to Booked Checkout #NOT NEEDED#,
    #  Booked Checkout to Available checkout
    # Done: The duration of this booking should be updated to booked, with guest and snake id updated against booking

    # cage = Cage.objects(id=cage.id)  # Refresh cage data
    available_booking_chosen: Booking = None
    initial_available_booking_list = cage.bookings
    for b in initial_available_booking_list:
        if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id is None:
            available_booking_chosen = b
            break

    # available_checkin = available_booking_chosen.check_in_date
    # available_checkout = available_booking_chosen.check_out_date
    # Above to be used for creating new available bookings once sanity added.

    if available_booking_chosen.check_in_date < checkin:
        new_prior_booking = add_available_date(
            cage=cage,
            start_date=available_booking_chosen.check_in_date,
            days=(checkin - available_booking_chosen.check_in_date).days
        )
    if available_booking_chosen.check_out_date > checkout:
        new_post_booking = add_available_date(
            cage=cage,
            start_date=checkout,
            days=(available_booking_chosen.check_out_date - checkout).days
        )
    available_booking_chosen.booked_date = datetime.datetime.now()
    available_booking_chosen.guest_snake_id = snake.id
    available_booking_chosen.guest_owner_id = account.id

    cage.save()
