""":mod:`langdev.thirdparty` --- Third-parties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LangDev provides a simple single sign-on API. It is available only for
registered third-party applications.

"""
import hmac
import hashlib
import datetime
from sqlalchemy import *
from sqlalchemy import orm
from sqlalchemy.sql import functions
import langdev.orm
import langdev.user


class Application(langdev.orm.Base):
    """A third-party application object."""

    def generate_key():
        """Generates a random :attr:`key`.

        :returns: a random-generated 32 characters
        :rtype: :class:`str`

        """
        return hashlib.md5(str(datetime.datetime.now())).hexdigest()

    def generate_secret_key():
        """Generates a random :attr:`secret_key`.

        :returns: a random-generated 64 characters
        :rtype: :class:`str`

        """
        return hashlib.sha256(str(datetime.datetime.now())).hexdigest()

    #: Unique primary key.
    key = Column(String(32), primary_key=True, default=generate_key)

    #: Secret key for :meth:`hmac()`.
    secret_key = Column(String(64), nullable=False,
                                    default=generate_secret_key)

    generate_key = staticmethod(generate_key)
    generate_secret_key = staticmethod(generate_secret_key)

    #: An :attr:`~langdev.user.User.id` of :attr:`owner`.
    owner_id = orm.deferred(Column(Integer, ForeignKey(langdev.user.User.id),
                                   nullable=False, index=True),
                            group='info')

    #: (:class:`~langdev.user.User`) An application owner.
    owner = orm.relationship(langdev.user.User,
                             backref=orm.backref('applications',
                                                 lazy='dynamic'))

    #: An application title.
    title = orm.deferred(Column(Unicode(100), nullable=False), group='info')

    #: A long description of the application.
    description = orm.deferred(Column(UnicodeText, nullable=False),
                               group='info')

    #: An application URL.
    url = orm.deferred(Column(UnicodeText, nullable=False), group='info')

    #: (:class:`datetime.datetime`) Created time.
    created_at = orm.deferred(Column(DateTime(timezone=True), nullable=False,
                                     default=functions.now()),
                              group='info')

    __tablename__ = 'applications'

    def hmac(self, string):
        """Hashes a :data:`string` using its :attr:`secret_key`.

        :param string: a string to hash
        :returns: a hashed hexadecimal digest of :data:`string` and
                  :attr:`secret_key`
        :rtype: :class:`str`

        """
        if isinstance(string, unicode):
            string = string.encode('utf-8')
        h = hmac.new(str(self.secret_key), str(string), hashlib.sha1)
        return h.hexdigest()

    def __unicode__(self):
        return self.title

