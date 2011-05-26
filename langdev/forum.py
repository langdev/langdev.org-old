""":mod:`langdev.forum` --- LangDev forum
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import *
from sqlalchemy import orm
from sqlalchemy.sql import functions
import langdev.orm
import langdev.user


class Post(langdev.orm.Base):
    """A forum post."""

    __tablename__ = 'posts'

    #: Unique primary key.
    id = Column(Integer, primary_key=True)

    #: An :attr:`~langdev.user.User.id` of :attr:`author`.
    author_id = Column(Integer, ForeignKey(langdev.user.User.id),
                       nullable=False, index=True)

    #: (:class:`~langdev.user.User`) A post author.
    author = orm.relationship(langdev.user.User,
                              innerjoin=True, lazy='dyanmic',
                              backref=orm.backref('posts', lazy='dynamic'))

    #: A post title.
    title = Column(Unicode(255), nullable=False, index=True)

    #: A post content.
    body = orm.deferred(Column(UnicodeText, nullable=False, index=True))

    #: Whether it is sticky.
    sticky = Column(Boolean, nullable=False, default=False, index=True)

    #: (:class:`datetime.datetime`) Created time.
    created_at = Column(DateTime(timezone=True),
                        nullable=False, default=functions.now(), index=True)

    #: (:class:`datetime.datetime`) Lastly modified time.
    modified_at = Column(DateTime(timezone=True), nullable=False,
                         default=functions.now(), onupdate=functions.now())

    @property
    def replies(self):
        """Comments that don't have :attr:`~Comment.parent` comments."""
        pid = Comment.parent_id
        return self.comments.filter((pid == None) | (pid == ''))

    def __unicode__(self):
        return self.title


class Comment(langdev.orm.Base):
    """A comment on a post."""

    __tablename__ = 'comments'

    #: Unique primary key.
    id = Column(Integer, primary_key=True)

    #: An :attr:`~Post.id` of :attr:`post`.
    post_id = Column(Integer, ForeignKey(Post.id), nullable=False, index=True)

    #: (:class:`Post`) A post this comment belongs to.
    post = orm.relationship(Post, innerjoin=True,
                            backref=orm.backref('comments', lazy='dynamic'))

    #: An :attr:`id` of :attr:`parent`.
    parent_id = Column(Integer, ForeignKey(id), default=None, index=True)

    #: Replies on this comment.
    replies = orm.relationship('Comment', innerjoin=True, lazy='dynamic',
                               backref=orm.backref('parent', remote_side=[id]))

    #: An :attr:`~langdev.user.User.id` of :attr:`author`.
    author_id = Column(Integer, ForeignKey(langdev.user.User.id),
                       nullable=False, index=True)

    #: (:class:`~langdev.user.User`) A comment author.
    author = orm.relationship(langdev.user.User,
                              backref=orm.backref('comments', lazy='dynamic'))

    #: A comment content.
    body = Column(UnicodeText, nullable=False, index=True)

    #: (:class:`datetime.datetime`) Created time.
    created_at = Column(DateTime(timezone=True),
                        nullable=False, default=functions.now(), index=True)

    def __unicode__(self):
        return self.body

