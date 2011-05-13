""":mod:`langdev.orm` --- Object-relational mapping powered by SQLAlchemy_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides object-relational mapping facilities powered by
SQLAlchemy_.

In order to define persist model class, just subclass :class:`Base`::

    from sqlalchemy import *
    import langdev.orm


    class Thing(langdev.orm.Base):
        '''A something object-relationally mapped.'''

        id = Column(Integer, primary_key=True)
        value = Column(UnicodeText, nullable=False)
        __tablename__ = 'things'

.. _SQLAlchemy: http://www.sqlalchemy.org/

"""
import sqlalchemy.orm
import sqlalchemy.ext.declarative


#: SQLAlchemy session class.
#:
#: .. seealso:: SQLAlchemy --- :ref:`session_toplevel`
Session = sqlalchemy.orm.sessionmaker(autocommit=True)

#: SQLAlchemy declarative base class.
#:
#: .. seealso:: SQLAlchemy --- :ref:`declarative_toplevel`
Base = sqlalchemy.ext.declarative.declarative_base()


def make_repr(self):
    """Make a :func:`repr()` string for the given ``self`` object.

    :param self: an object to make a :func:`repr()` string
    :returns: a :func:`repr()` string
    :rtype: :class:`str`

    """
    cls = type(self)
    mod = cls.__module__
    name = ('' if mod == '__main__ ' else mod + '.') + cls.__name__
    args = ', '.join(pk.name + '=' + repr(getattr(self, pk.name))
                     for pk in cls.__mapper__.primary_key)
    return '<{0} {1}>'.format(name, args)


Base.__repr__ = make_repr

