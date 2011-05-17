""":mod:`langdev.web.forum` --- Forum pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import math
from flask import *
from flaskext.wtf import *
from langdev.forum import Post, Comment
from langdev.web import render
import langdev.web.user
import langdev.web.pager


#: Forum web pages module.
#:
#: .. seealso:: Flask --- :ref:`working-with-modules`
forum = Module(__name__)


def get_post(post_id):
    try:
        return g.session.query(Post).filter_by(id=post_id)[0]
    except IndexError:
        abort(404)


@forum.route('/')
def posts():
    posts = g.session.query(Post) \
                     .order_by(Post.sticky.desc(), Post.created_at.desc())
    cnt = posts.count()
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))
    posts = posts.offset(offset).limit(limit)
    pager = langdev.web.pager.Pager(math.ceil(cnt / float(limit)),
                                    1 + offset / limit)
    return render('forum/posts', posts, posts=posts, pager=pager, limit=limit)


@forum.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render('forum/post', post, post=post)


class PostForm(Form):
    title = TextField('Title', validators=[Required()])
    body = TextAreaField('Body', validators=[Required()])
    sticky = BooleanField('Sticky')
    submit = SubmitField('Submit')


@forum.route('/write')
def write_form(form=None):
    langdev.web.user.ensure_signin()
    form = form or PostForm()
    return render('forum/write_form', form, form=form)


@forum.route('/', methods=['POST'])
def write():
    langdev.web.user.ensure_signin()
    form = PostForm()
    if form.validate():
        post = Post(author=g.current_user)
        form.populate_obj(post)
        with g.session.begin():
            g.session.add(post)
        return redirect(url_for('post', post_id=post.id), 302)
    return write_form(form=form)


@forum.route('/<int:post_id>/edit')
def edit_form(post_id, form=None):
    post = get_post(post_id)
    langdev.web.user.ensure_signin(post.author)
    form = form or PostForm(request.form, post)
    return render('forum/edit_form', form, form=form, post=post)


@forum.route('/<int:post_id>', methods=['PUT'])
def edit(post_id):
    post_object = get_post(post_id)
    langdev.web.user.ensure_signin(post_object.author)
    form = PostForm()
    if form.validate():
        with g.session.begin():
            form.populate_obj(post_object)
        return post(post_object.id)
    return render('forum/edit_form', form, form=form)

