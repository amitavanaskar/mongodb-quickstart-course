import mongoengine


class Booking(mongoengine.EmbeddedDocument):
    guest_owner_id = mongoengine.ObjectIdField()  # Usually when we refer of IDs, in mongoDB it is object id field
    guest_snake_id = mongoengine.ObjectIdField()

    booked_date = mongoengine.DateTimeField()
    # This cannot be a required field as this would be generated when a booking is created
    check_in_date = mongoengine.DateTimeField(required=True)
    check_out_date = mongoengine.DateTimeField(required=True)

    review = mongoengine.StringField()
    rating = mongoengine.IntField(default=0)    # Can ask to rate from 1-5, filter out the zeroes for avg (not rated)

    # meta = {
    #     'db_alias': 'core',
    #     'collection': 'cages'
    # }
# Meta details not needed as this is an embedded document.