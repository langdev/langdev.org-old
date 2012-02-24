""":mod:`langdev.web.user` --- User web pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attribute:: flask.g.current_user

   The global variable that stores the currently signed
   :class:`~langdev.user.User` object.

"""
import re
import time
import datetime
import hmac
import hashlib
import textwrap
from flask import (Blueprint, request, session, g, abort, redirect,
                   url_for, current_app)
from flask.ext import wtf
from flask.ext.mail import Message
from sqlalchemy import orm
from langdev.user import User
from langdev.web import before_request, errorhandler, render
from langdev.objsimplify import Result


#: User web pages blueprint.
#:
#: .. seealso:: Flask --- :ref:`modular-applications-with-blueprints`
user = Blueprint('user', __name__)


@before_request
def define_current_user():
    """Sets the :attr:`g.current_user <flask.g.current_user>` global variable
    before every request.

    """
    try:
        user_id = session['user_id']
    except KeyError:
        g.current_user = None
    else:
        g.current_user = g.session.query(User).filter_by(id=user_id).first()


@user.app_context_processor
def inject_current_user():
    """Injects the :attr:`current_user <flask.g.current_user>` for templates.
    
    .. sourcecode:: html+jinja

       {% if current_user %}
         <p>You are {{ current_user }}.</p>
       {% else %}
         <p>Who are you?</p>
       {% endif %}

    """
    return {'current_user': g.current_user}


def set_current_user(user):
    """Sets the :attr:`g.current_user <flask.g.current_user>`. ``user`` can
    be ``None`` also.

    :param user: the user to set. signs out if it is ``None``
    :type user: :class:`~langdev.user.User`, :class:`types.NoneType`

    """
    if user is None:
        del session['user_id']
        return
    if not isinstance(user, User):
        raise TypeError('expected a langdev.user.User instance, not ' +
                        repr(user))
    session['user_id'] = user.id


def ensure_signin(user=None):
    """Raises a 403 :exc:`~werkzeug.exceptions.Forbidden` error if not signed
    in or :attr:`g.current_user <flask.g.current_user>` is not ``user``
    (only if a parameter has passed).

    :param user: an optional user. if present, it checks signed user's
                 identity also
    :type user: :class:`~langdev.user.User`
    :returns: a signed user
    :rtype: :class:`~langdev.user.User`

    """
    if not g.current_user or user and g.current_user.id != user.id:
        abort(403)
    return g.current_user


@errorhandler(403)
def forbidden(error):
    """403 forbidden page."""
    if g.current_user:
        return 'Forbidden', 403
    return signin_form(return_url=request.url)


@user.route('/f/signout')
def signout():
    """Signs out."""
    return_url = request.args.get('return_url',
                                  request.referrer or url_for('home.main'))
    set_current_user(None)
    return redirect(return_url)


class SignInForm(wtf.Form):

    login = wtf.TextField('Login name',
                          validators=[wtf.Required(), wtf.Length(2, 45),
                                      wtf.Regexp(User.LOGIN_PATTERN)])
    password = wtf.PasswordField('Password', validators=[wtf.Required()])
    return_url = wtf.HiddenField(validators=[wtf.Optional()])
    submit = wtf.SubmitField('Login')

    def validate_login(form, field):
        if g.session.query(User).filter_by(login=field.data).count() < 1:
            raise wtf.ValidationError('There is no {0}.'.format(field.data))

    def validate_password(form, field):
        try:
            user = g.session.query(User).filter_by(login=form.login.data)[0]
        except IndexError:
            pass
        else:
            if user.password != field.data:
                raise wtf.ValidationError('Incorrect password.')


@user.route('/f/signin')
def signin_form(form=None, return_url=None):
    if not form:
        form = SignInForm()
        return_url = return_url or request.values.get('return_url')
        if return_url:
            form.return_url.data = return_url
    return render('user/signin_form', form, form=form)


@user.route('/f/signin', methods=['POST'])
def signin():
    form = SignInForm()
    if form.validate():
        user = g.session.query(User).filter_by(login=form.login.data)[0]
        set_current_user(user)
        return_url = form.return_url.data or \
                     url_for('.profile', user_login=user.login)
        return redirect(return_url)
    return signin_form(form=form)


class SignUpForm(wtf.Form):

    login = wtf.TextField('Login name',
                          validators=[wtf.Required(), wtf.Length(2, 45),
                                      wtf.Regexp(User.LOGIN_PATTERN)])
    password = wtf.PasswordField(
        'Password',
        validators=[wtf.Required(),
                    wtf.EqualTo('confirm', message='Passwords must match.')]
    )
    confirm = wtf.PasswordField('Repeat Password', validators=[wtf.Required()])
    name = wtf.TextField('Screen name',
                         validators=[wtf.Required(), wtf.Length(1, 45)])
    email = wtf.html5.EmailField('Email',
                                 validators=[wtf.Optional(), wtf.Email()])
    url = wtf.html5.URLField('Website', validators=[wtf.Optional(), wtf.URL()])

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if ('RECAPTCHA_PUBLIC_KEY' in current_app.config and
            'RECAPTCHA_PRIVATE_KEY' in current_app.config):
            class SignUpForm_recaptcha(cls):
                recaptcha = wtf.RecaptchaField()
                submit = wtf.SubmitField('Sign up')
            return SignUpForm_recaptcha(*args, **kwargs)
        class SignUpForm_plain(cls):
            submit = wtf.SubmitField('Sign up')
        return SignUpForm_plain(*args, **kwargs)

    def validate_login(form, field):
        if g.session.query(User).filter_by(login=field.data).count():
            raise wtf.ValidationError(
                '{0} is already taken.'.format(field.data))


class ProfileForm(wtf.Form):

    password = wtf.PasswordField(
        'Password',
        validators=[wtf.Required(),
                    wtf.EqualTo('confirm', message='Passwords must match.')]
    )
    confirm = wtf.PasswordField('Repeat Password', validators=[wtf.Required()])
    name = wtf.TextField('Screen name',
                         validators=[wtf.Required(), wtf.Length(1, 45)])
    email = wtf.html5.EmailField('Email',
                                 validators=[wtf.Optional(), wtf.Email()])
    url = wtf.html5.URLField('Website', validators=[wtf.Optional(), wtf.URL()])
    submit = wtf.SubmitField('Save')


@user.route('/f/signup')
def signup_form(form=None):
    form = form or SignUpForm.get_instance()
    response = render('user/signup_form', form, form=form)
    # ReCAPTCHA doesn't work on application/xhtml+xml.
    if ('RECAPTCHA_PUBLIC_KEY' in current_app.config and
        'RECAPTCHA_PRIVATE_KEY' in current_app.config and
        re.match(r'^application/xhtml\+xml(;|$)', response.content_type)):
        response.content_type = 'text/html'
    return response


@user.route('/', methods=['POST'])
def signup():
    form = SignUpForm.get_instance()
    if form.validate():
        user = User(login=request.form['login'].strip(),
                    password=request.form['password'],
                    name=request.form['name'].strip(),
                    email=request.form['email'].strip(),
                    url=request.form['url'].strip())
        with g.session.begin():
            g.session.add(user)
        set_current_user(user)
        return redirect(url_for('.profile', user_login=user.login), 302)
    return signup_form(form=form)


def get_user(login, *options):
    """Gets a user by its ``login`` name."""
    query = g.session.query(User).filter_by(login=login)
    for option in options:
        query = query.options(option)
    try:
        return query[0]
    except IndexError:
        abort(404)


@user.route('/<user_login>')
def profile(user_login, form=None):
    """User profile page."""
    user = get_user(user_login)
    if g.current_user == user and not form:
        form = ProfileForm(request.form, user)
    return render('user/profile', user, user=user, form=form)


@user.route('/<user_login>', methods=['PUT'])
def edit(user_login):
    """Edit the profile."""
    user = get_user(user_login)
    ensure_signin(user)
    form = ProfileForm()
    if form.validate():
        with g.session.begin():
            form.populate_obj(user)
        return profile(user_login)
    return profile(user_login, form)


@user.route('/<user_login>', methods=['DELETE'])
def leave(user_login):
    user = get_user(user_login)
    ensure_signin(user)
    with g.session.begin():
        g.session.delete(user)
    set_current_user(None)
    return_url = request.values.get('return_url')
    if return_url:
        return redirect(return_url)
    return ''


@user.route('/<user_login>/posts')
def posts(user_login):
    """Posts a user wrote."""
    user = get_user(user_login)
    posts = user.posts
    return render('user/posts', posts, user=user, posts=posts)


class PasswordFindingForm(wtf.Form):

    login = wtf.TextField('Login name',
                          validators=[wtf.Required(), wtf.Length(2, 45),
                                      wtf.Regexp(User.LOGIN_PATTERN)])
    submit = wtf.SubmitField('Find')

    def validate_login(form, field):
        if g.session.query(User).filter_by(login=field.data).count() < 1:
            raise wtf.ValidationError('There is no {0}.'.format(field.data))


@user.route('/f/orgot')
def find_password_form(form=None):
    form = form or PasswordFindingForm()
    return render('user/find_password_form', form, form=form)


@user.route('/f/orgot', methods=['POST'])
def find_password():
    form = PasswordFindingForm()
    if form.validate():
        url = url_for('user.request_find_password',
                      user_login=form.data['login'])
        return redirect(url, 307)
    return find_password_form(form=form)


def generate_token(user, expiration=3600 * 6):
    expired_at = int(time.time()) + expiration
    expired_at_hex = hex(expired_at)[2:]
    sumstr = '{0},{1},{2}'.format(user.id, str(user.password), expired_at)
    checksum = hmac.new(current_app.secret_key, sumstr, hashlib.sha1)
    return checksum.hexdigest() + expired_at_hex, expired_at


def is_token_expired(user, token):
    if len(token) < 41:
        abort(404)
    checksum = token[:40]
    expired_at = int(token[40:], 16)
    sumstr = '{0},{1},{2}'.format(user.id, str(user.password), expired_at)
    checksum2 = hmac.new(current_app.secret_key, sumstr, hashlib.sha1)
    if checksum != checksum2.hexdigest():
        abort(404)
    return expired_at < time.time()


def hide_email(email):
    """Hides an email address.

    .. sourcecode:: pycon

       >>> hide_email('hong.qigong@gaibang.org.cn')
       'h***.******@*******.***.*n'
       >>> hide_email('amaterasu+ladios.sopp@akd.gov')
       'a********+******.****@***.**v'
       >>> hide_email('ab@cd.co.kr')
       'a*@**.**.*r'

    :param email: an email address to hide
    :type email: :class:`basestring`
    :returns: a hidden email address
    :rtype: :class:`basestring`

    """
    hidden = re.sub(r'[^.+@]', '*', email)
    return email[0] + hidden[1:-1] + email[-1]


@user.route('/<user_login>/password-findings')
def request_find_password_form(user_login):
    user = get_user(user_login)
    return render('user/request_find_password_form', user, user=user)


@user.route('/<user_login>/password-findings', methods=['POST'])
def request_find_password(user_login):
    user = get_user(user_login, orm.undefer_group('profile'))
    if user.email:
        token, expired_at = generate_token(user)
        url = url_for('.change_password_form',
                      user_login=user.login, token=token, _external=True)
        expired_at = datetime.datetime.utcfromtimestamp(expired_at)
        msg = Message('[LangDev.org] Change your password: ' + user.login,
                      recipients=[user.email])
        msg.body = textwrap.dedent('''
            You can change your password through the following link:
            {url}

            But the above link will be expired at {expired_at} UTC.
        ''').format(url=url, expired_at=expired_at)
        current_app.mail.send(msg)
        email = hide_email(user.email)
        result = Result(user=user, email=email)
        status_code = 201
    else:
        result = Result(user=user, error='Has no email address')
        status_code = 403
    response = render('user/request_find_password', result, **result)
    response.status_code = status_code
    return response


class ChangePasswordForm(wtf.Form):

    password = wtf.PasswordField(
        'Password',
        validators=[wtf.Required(),
                    wtf.EqualTo('confirm', message='Passwords must match.')]
    )
    confirm = wtf.PasswordField('Repeat Password', validators=[wtf.Required()])
    submit = wtf.SubmitField('Save')


@user.route('/<user_login>/password-findings/<token>')
def change_password_form(user_login, token, form=None):
    user = get_user(user_login)
    expired = is_token_expired(user, token)
    form = form or ChangePasswordForm()
    response = render('user/change_password_form', form,
                      form=form, user=user, token=token, expired=expired)
    if expired:
        response.status_code = 403
    return response


@user.route('/<user_login>/password-findings/<token>', methods=['POST'])
def change_password(user_login, token):
    user = get_user(user_login)
    form = ChangePasswordForm()
    if not is_token_expired(user, token) and form.validate():
        with g.session.begin():
            form.populate_obj(user)
        return render('user/change_password', user, user=user)
    return change_password_form(user_login=user_login, token=token, form=form)

