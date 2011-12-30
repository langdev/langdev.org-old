""":mod:`langdev.user` --- LangDev users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides user and authentication facilities that is service-agnostic.
Many services for LangDev can provide single sign on based on this module.

.. sourcecode:: pycon

   >>> sess = langdev.orm.Session()  # doctest: +SKIP
   >>> sess.query(User).filter_by(login=u'dahlia')[0]  # doctest: +SKIP
   <langdev.user.User id=1>

"""
import re
import hashlib
from sqlalchemy import *
from sqlalchemy import orm
from sqlalchemy.sql import functions
import langdev.orm

__all__ = 'User', 'Password'


class User(langdev.orm.Base):
    """An user object."""

    #: The :mod:`re` pattern that matches to valid login names.
    LOGIN_PATTERN = re.compile(ur'^[-_.a-z0-9\u1100-\u11ff\u3131-\u318e'
                               ur'\u3200-\u321e\u3260-\u327e\ua960-\ua97c'
                               ur'\uac00-\ud7a3\ud7b0-\ud7c6\ud7cb-\ud7fb'
                               ur'\uffa0-\uffbe\uffc2-\uffc7\uffca-\uffcf'
                               ur'\uffd2-\uffd7\uffda-\uffdc]{2,45}$')

    #: The :mod:`re` pattern that matches to valid email addresses.
    EMAIL_PATTERN = re.compile(ur"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+"
                               ur"(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
                               ur'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)'
                               ur'+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$',
                               re.IGNORECASE)

    __tablename__ = 'users'

    #: Unique primary key.
    id = Column(Integer, primary_key=True)

    #: Login name.
    login = Column(Unicode(45), nullable=False, unique=True)

    #: Hashed password.
    password_hash = orm.deferred(Column(String(32), nullable=False))

    #: Screen name.
    name = Column(Unicode(45), nullable=False, index=True)

    #: Email address.
    email = orm.deferred(Column(Unicode(255), index=True), group='profile')

    #: His/her website.
    url = orm.deferred(Column(UnicodeText, index=True), group='profile')

    #: (:class:`datetime.datetime`) Registered time.
    created_at = orm.deferred(Column(DateTime(timezone=True), nullable=False,
                                     default=functions.now(), index=True),
                              group='profile')

    @orm.validates(login)
    def validate_login(self, key, login):
        """Validates the :attr:`login` name format.

        :raises: :exc:`~exceptions.ValueError` when it's invalid

        """
        if login is None:
            return
        login = login.strip().lower()
        if self.LOGIN_PATTERN.match(login):
            return login
        raise ValueError('{0!r} is an invalid login name'.format(login))

    @orm.validates(email)
    def validate_email(self, key, email):
        """Validates the :attr:`email` format.

        :raises: :exc:`~exceptions.ValueError` when it's invalid

        """
        if email is None:
            return
        email = email.strip()
        if self.EMAIL_PATTERN.match(email):
            return email
        raise ValueError('{0!r} is an invalid email address'.format(email))

    @property
    def password(self):
        """:class:`Password`."""
        return Password(self.password_hash)

    @password.setter
    def password(self, password):
        if isinstance(password, Password):
            self.password_hash = password.hash_string
        elif isinstance(password, basestring):
            self.password_hash = Password.hash_algorithm(password).hexdigest()
        else:
            raise TypeError('password have to be a string, not ' +
                            repr(password))

    def __unicode__(self):
        return self.name
            

class Password(object):
    """Tests two passwords' equality. It overloads ``==`` and ``!=`` operators.
    Stripped password string can be an operand.

    .. sourcecode:: pycon

       >>> u = User(login=u'test-for-password',
       ...          name=u'Test for password',
       ...          password=u'password string')
       >>> u.password == u'password string'
       True
       >>> u.password != u'wrong password'
       True

    Of cource, :class:`Password` can be an operand also:

    .. sourcecode:: pycon

       >>> u.password == u.password
       True
       >>> u.password != u.password
       False

    :param hash_string: a hashed password string
    :type hash_string: :class:`str`

    """

    #: UTF-8 by default.
    ENCODING = 'utf-8'

    #: Hashed password string.
    hash_string = None

    #: Hash algorithm. MD5 is used.
    hash_algorithm = hashlib.md5

    def __init__(self, hash_string):
        if isinstance(hash_string, unicode):
            hash_string = hash_string.encode(self.ENCODING)
        elif not isinstance(hash_string, str):
            raise TypeError(repr(hash_string) +
                            ' is a invalid type for hash_string')
        self.hash_string = hash_string

    def __eq__(self, password):
        if isinstance(password, type(self)):
            return self.hash_string == password.hash_string
        elif isinstance(password, unicode):
            password = password.encode(self.ENCODING)
        if not isinstance(password, str):
            return False
        return self.hash_algorithm(password).hexdigest() == self.hash_string

    def __ne__(self, password):
        return not (self == password)

    def __hash__(self):
        return hash(self.hash_string)

    def __str__(self):
        return self.hash_string

    def __repr__(self):
        return '<{0}.Password {1!r}>'.format(__name__, self.hash_string)

