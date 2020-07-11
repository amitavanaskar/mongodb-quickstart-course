import mongoengine
import datetime


class Snake(mongoengine.Document): # Tells mongoengine that owners is a top level document
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)
    # We are passing the function, not the value of now. Adding parenthesis in now() would pass the time when the
    # program started.
    species = mongoengine.StringField(required=True)

    length = mongoengine.FloatField(required=True, min_value=0.001)
    name = mongoengine.StringField(required=True)
    is_venomous = mongoengine.BooleanField(required=True)

    meta = {
        'db_alias': 'core',
        'collection': 'snakes'
    }


"""
Note - MongoDB does not have constraints like required field. That is provided by MongoEngine.
"""
