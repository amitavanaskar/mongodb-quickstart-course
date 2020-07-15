import mongoengine
import datetime

from data.bookings import Booking


class Cage(mongoengine.Document):  # This tells mongoengine that this is a top level document
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)

    name = mongoengine.StringField(required=True)
    price = mongoengine.FloatField(required=True)
    square_meters = mongoengine.FloatField(required=True)
    is_carpeted = mongoengine.BooleanField(required=True)
    has_toys = mongoengine.BooleanField(required=True)
    allow_dangerous_snakes = mongoengine.BooleanField(required=True, default=False)

    bookings = mongoengine.EmbeddedDocumentListField(Booking)
    # Passing bookings as an embedded document of type list with input from Booking

    meta = {
        'db_alias': 'core',
        'collection': 'cages'
    }
