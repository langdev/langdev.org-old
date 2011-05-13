""":mod:`langdev.web.home` --- Website home
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import *


#: Home module.
#:
#: .. seealso:: Flask --- :ref:`working-with-modules`
home = Module(__name__)


@home.route('/')
def main():
    if g.current_user:
        url = url_for('user.profile', user_login=g.current_user.login)
    else:
        url = url_for('user.signin_form')
    return redirect(url)

