""":mod:`langdev.web.user` --- User web pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attribute:: flask.g.current_user

   The global variable that stores the currently signed
   :class:`~langdev.user.User` object.

"""
import re
import urllib2
import werkzeug.urls
from flask import *
from langdev.user import User
from langdev.web import before_request, render


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


@user.route('/f/signout')
def signout():
    """Signs out."""
    return_url = request.args.get('return_url',
                                  request.referrer or url_for('home.main'))
    set_current_user(None)
    return redirect(return_url)


@user.route('/f/signin')
def signin_form(error=False):
    return render('user/signin_form', not error, error=error)


@user.route('/f/signin', methods=['POST'])
def signin():
    login = request.form['login'].strip().lower()
    password = request.form['password']
    try:
        user = g.session.query(User).filter_by(login=login)[0]
    except IndexError:
        pass
    else:
        if user.password == password:
            set_current_user(user)
            return redirect(url_for('profile', user_login=user.login))
    return signin_form(error=True)


@user.route('/f/signup')
def signup_form(recaptcha_error=None):
    # ReCAPTCHA doesn't work on application/xhtml+xml.
    response = render('user/signup_form', None,
                      recaptcha_error=recaptcha_error)
    if ('RECAPTCHA_PUBLIC_KEY' in current_app.config and
        'RECAPTCHA_PRIVATE_KEY' in current_app.config and
        re.match(r'^application/xhtml\+xml(;|$)', response.content_type)):
        response.content_type = 'text/html'
    return response


@user.route('/', methods=['POST'])
def signup():
    if ('RECAPTCHA_PUBLIC_KEY' in current_app.config and
        'RECAPTCHA_PRIVATE_KEY' in current_app.config):
        r_params = {'privatekey': current_app.config['RECAPTCHA_PRIVATE_KEY'],
                    'remoteip': request.remote_addr,
                    'challenge': request.form['recaptcha_challenge_field'],
                    'response': request.form['recaptcha_response_field']}
        r = urllib2.urlopen('http://www.google.com/recaptcha/api/verify',
                            data=werkzeug.urls.url_encode(r_params))
        result = r.readlines()
        if result[0].strip() == 'false':
            response = signup_form(recaptcha_error=result[1].strip())
            response.status_code = 400
            return response
    user = User(login=request.form['login'].strip(),
                password=request.form['password'],
                name=request.form['name'].strip(),
                email=request.form['email'].strip(),
                url=request.form['url'].strip())
    with g.session.begin():
        g.session.add(user)
    set_current_user(user)
    return redirect(url_for('profile', user_login=user.login), 302)


@user.route('/<user_login>')
def profile(user_login):
    """User profile page."""
    try:
        user = g.session.query(User).filter_by(login=user_login)[0]
    except IndexError:
        abort(404)
    return render('user/profile', user, user=user)

