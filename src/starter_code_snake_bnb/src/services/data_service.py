import datetime
from typing import List

from data.bookings import Booking
from data.cages import Cage
from data.owners import Owner


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
active_account: Owner, sq_meters: float, carpeted: bool, has_toys: bool, allow_dangerous: bool, price: float, name: str
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
    account = find_account_by_email(active_account.email)   # Ensures no stale data (Instead of using account directly)
    account.cage_ids.append(cage.id)    # Called save earlier ensures that the cage id is generated
    account.save()  # Pushing the changes we have made to the account to the db

    return cage


def find_cages_for_user(account: Owner) -> List[Cage]:  # Pycharm Tip: Alt + Enter > Typing module choose list
    query = Cage.objects(id__in=account.cage_ids)   # __ is used in mongoengine to leverage mondodb's $ operators
    # Here it will retrieve Cage objects where the cage id is owner's cage_id list
    cages = list(query)     # Executing the query and snapshot it for the app
    return cages


def add_available_date(cage: Cage, start_date: datetime.datetime, days: int) -> Cage:
    booking = Booking()
    booking.check_in_date = start_date
    booking.check_out_date = start_date + datetime.timedelta(days=days)

    cage = Cage.objects(id=cage.id).first()
    cage.bookings.append(booking)   # Bookings are not top level items. They are present inside cages
    cage.save()     # Save cages

    return cage