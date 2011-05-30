""":mod:`langdev.web.user` --- User web pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attribute:: flask.g.current_user

   The global variable that stores the currently signed
   :class:`~langdev.user.User` object.

"""
import re
from flask import *
from flaskext.wtf import *
import werkzeug.datastructures
from langdev.user import User
from langdev.web import before_request, errorhandler, render


#: User web pages module.
#:
#: .. seealso:: Flask --- :ref:`working-with-modules`
user = Module(__name__)


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


class SignInForm(Form):

    login = TextField('Login name',
                      validators=[Required(), Length(2, 45),
                                  Regexp(User.LOGIN_PATTERN)])
    password = PasswordField('Password', validators=[Required()])
    return_url = HiddenField(validators=[Optional()])
    submit = SubmitField('Login')

    def validate_login(form, field):
        if g.session.query(User).filter_by(login=field.data).count() < 1:
            raise ValidationError('There is no {0}.'.format(field.data))

    def validate_password(form, field):
        try:
            user = g.session.query(User).filter_by(login=form.login.data)[0]
        except IndexError:
            pass
        else:
            if user.password != field.data:
                raise ValidationError('Incorrect password.')


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
                     url_for('profile', user_login=user.login)
        return redirect(return_url)
    return signin_form(form=form)


class SignUpForm(Form):

    login = TextField('Login name',
                      validators=[Required(), Length(2, 45),
                                  Regexp(User.LOGIN_PATTERN)])
    password = PasswordField(
        'Password',
        validators=[Required(), EqualTo('confirm',
                                        message='Passwords must match.')]
    )
    confirm = PasswordField('Repeat Password', validators=[Required()])
    name = TextField('Screen name', validators=[Required(), Length(1, 45)])
    email = html5.EmailField('Email', validators=[Optional(), Email()])
    url = html5.URLField('Website', validators=[Optional(), URL()])

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if ('RECAPTCHA_PUBLIC_KEY' in current_app.config and
            'RECAPTCHA_PRIVATE_KEY' in current_app.config):
            class SignUpForm_recaptcha(cls):
                recaptcha = RecaptchaField()
                submit = SubmitField('Sign up')
            return SignUpForm_recaptcha(*args, **kwargs)
        class SignUpForm_plain(cls):
            submit = SubmitField('Sign up')
        return SignUpForm_plain(*args, **kwargs)

    def validate_login(form, field):
        if g.session.query(User).filter_by(login=field.data).count():
            raise ValidationError('{0} is already taken.'.format(field.data))


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
        return redirect(url_for('profile', user_login=user.login), 302)
    return signup_form(form=form)


def get_user(login):
    """Gets a user by its ``login`` name."""
    try:
        return g.session.query(User).filter_by(login=login)[0]
    except IndexError:
        abort(404)


@user.route('/<user_login>')
def profile(user_login):
    """User profile page."""
    user = get_user(user_login)
    return render('user/profile', user, user=user)


@user.route('/<user_login>/posts')
def posts(user_login):
    """Posts a user wrote."""
    user = get_user(user_login)
    posts = user.posts
    return render('/user/posts', posts, user=user, posts=posts)

