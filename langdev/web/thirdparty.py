""":mod:`langdev.web.thirdparty` --- Third-party applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import re
from flask import *
from flaskext.wtf import *
import werkzeug.exceptions
import sqlalchemy.orm.exc
from langdev.user import User
from langdev.thirdparty import Application
from langdev.web import render
import langdev.web.user


#: Third-party application pages blueprint.
#:
#: .. seealso:: Flask --- :ref:`flask:blueprints`
thirdparty = Blueprint('thirdparty', __name__)


class ApplicationForm(Form):

    title = TextField('Application title',
                      validators=[Required(), Length(2, 100)])
    url = html5.URLField('Application website', validators=[Required()])
    description = TextAreaField('Description', validators=[Required()])
    submit = SubmitField('Create application')


@thirdparty.route('/')
def register_form(form=None):
    """Third-party application registration form."""
    langdev.web.user.ensure_signin()
    form = form or ApplicationForm()
    return render('thirdparty/register_form', form, form=form)


@thirdparty.route('/', methods=['POST'])
def register():
    langdev.web.user.ensure_signin()
    form = ApplicationForm()
    if form.validate():
        app = Application(owner=g.current_user)
        form.populate_obj(app)
        with g.session.begin():
            g.session.add(app)
        return redirect(url_for('.app', app_key=app.key), 302)
    return register_form(form=form)


def get_app(key):
    """Gets an application by its :data:`~langdev.thirdparty.Application.key`.

    :param key: :data:`Application.key <langdev.thidparty.Application.key>`
                to find
    :type key: :class:`str`
    :returns: a found application
    :rtype: :class:`langdev.thirdparty.Application`

    """
    try:
        return g.session.query(Application).filter_by(key=key)[0]
    except IndexError:
        abort(404)


@thirdparty.route('/<app_key>')
def app(app_key):
    """Application detail information."""
    app = get_app(app_key)
    langdev.web.user.ensure_signin(app.owner)
    return render('thirdparty/app', app, app=app)


@thirdparty.route('/<app_key>', methods=['DELETE'])
def delete_app(app_key):
    """Deletes an application."""
    app = get_app(app_key)
    langdev.web.user.ensure_signin(app.owner)
    with g.session.begin():
        g.session.delete(app)
    return redirect(url_for('.register'), 302)


@thirdparty.route('/<app_key>/sso/<user_login>', methods=['GET', 'POST'])
def sso(app_key, user_login):
    """Simple SSO API."""
    app = get_app(app_key)
    require_userinfo = request.values.get('with') == 'userinfo'
    error_ignored = request.values.get('error') == 'ignore'
    success = None
    if User.LOGIN_PATTERN.match(user_login):
        try:
            user = langdev.web.user.get_user(user_login)
        except werkzeug.exceptions.NotFound:
            if not error_ignored:
                raise
            success = False
    else:
        try:
            user = g.session.query(User).filter_by(email=user_login).one()
        except sqlalchemy.orm.exc.NoResultFound:
            if error_ignored:
                success = False
            else:
                abort(404)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            success = False
    if success is None:
        success = app.hmac(user.password) == request.values['password']
    if success and require_userinfo:
        result = user
        # workaround to include ``email`` attribute in the response.
        # see also :func:`langdev.objsimplify.transform`.
        g.current_user = user
    else:
        result = success
    return render('thirdparty/sso', result, success=success)

