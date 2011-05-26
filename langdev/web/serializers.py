""":mod:`langdev.web.serializers` --- Serializers for various content types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import types
import datetime
import plistlib
import flask
import langdev.user
from langdev.objsimplify import *


def json(value):
    """Serializes a ``value`` into JSON (:mimetype:`application/json`).

    :param value: a value to serialize to JSON
    :returns: a serialized JSON string
    :rtype: :class:`basestring`

    """
    type_map = {datetime.datetime: datetime.datetime.isoformat,
                datetime.date: datetime.date.isoformat}
    data = simplify(value, identifier_map=camelCase,
                           type_map=type_map,
                           user=flask.g.current_user)
    return flask.json.dumps(data)


def plist(value):
    """Serializes a ``value`` into property list (plist) format.
    (:mimetype:`application/plist+xml`)

    :param value: a value to serialize to plist
    :returns: a serialized plist XML
    :rtype: :class:`basestring`

    """
    type_map = {datetime.date: datetime.date.isoformat,
                types.NoneType: bool}
    data = simplify(value, identifier_map=PascalCase,
                           type_map=type_map,
                           user=flask.g.current_user)
    return plistlib.writePlistToString(data)

