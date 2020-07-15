import mongoengine


def global_init():
    mongoengine.register_connection(alias='core', name='snake_bnb')
    # We can have multiple connections, multiple databases or multiple database servers too registered in an alias.
    # For real production connections, port, username, password, authentication mechanisms, authentication sources etc
    # would need to be added.
    # This needs to be called once across the application to setup connection with the mongodb
