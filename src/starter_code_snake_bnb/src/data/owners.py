import mongoengine
import datetime


class Owner(mongoengine.Document):
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)
    name = mongoengine.StringField(required=True)
    email = mongoengine.EmailField(required=True)

    snake_ids = mongoengine.ListField()  # When we refer to IDs, in mongoDB it is usually object ID field.
    cage_ids = mongoengine.ListField()  # In this case we need to have a list of all snakes and cages.

    meta = {
        'db_alias': 'core',
        'collection': 'owners'
    }
