#!/usr/bin/env python
""":mod:`manage_langdev` --- LangDev manager script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import sys
import os.path
import hashlib
import datetime
import flask
from flaskext.script import *
import langdev.orm
import langdev.web
import langdev.user


model_modules = ['langdev.user', 'langdev.forum', 'langdev.thirdparty']


def create_app(config_filename):
    if not os.path.isfile(config_filename):
        msg = "{0} doesn't exist yet; would you create it"
        creating = prompt_bool(msg.format(config_filename), default=True)
        if creating:
            create_config_file(config_filename)
    if not os.path.isfile(config_filename):
        print>>sys.stderr, "{0} doesn't exist".format(config_filename)
        raise SystemExit
    return langdev.web.create_app(config_filename=config_filename)


manager = Manager(create_app)
manager.add_option('-c', '--config', dest='config_filename', required=True)


def create_config_file(config_filename):
    """Creates a new config file."""
    current_path = os.path.abspath('.')
    with open(config_filename, 'w') as config:
        database_url = 'sqlite:///{0}/db.sqlite'.format(current_path)
        database_url = prompt('Database URL', default=database_url)
        print>>config, 'DATABASE_URL =', repr(database_url)
        secret_key = hashlib.md5(`datetime.datetime.now()`).hexdigest()
        secret_key = prompt('Secret key for secure session',
                            default=secret_key)
        print>>config, 'SECRET_KEY =', repr(secret_key)
        intersites = []
        if prompt_bool('Are there any external sites to link', default=False):
            while True:
                key = prompt('External site name')
                value = prompt('URL of ' + key)
                intersites.append((key, value))
                if not prompt_bool('Are there remaining external sites',
                                   default=False):
                    break
        print>>config, 'INTERSITES =', repr(intersites)
    print '{0} config file has created'.format(config_filename)


@manager.command
def initdb():
    """Creates all tables needed by LangDev."""
    for module in model_modules:
        __import__(module)
    engine = langdev.web.get_database_engine(flask.current_app.config)
    langdev.orm.Base.metadata.create_all(engine)


@manager.shell
def make_shell_context():
    engine = langdev.web.get_database_engine(flask.current_app.config)
    return {'app': flask.current_app, 'g': flask.g,
            'engine': engine, 'session': langdev.orm.Session(bind=engine),
            'langdev': langdev, 'User': langdev.user.User}


if __name__ == '__main__':
    manager.run()

