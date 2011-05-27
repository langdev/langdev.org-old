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
    return redirect(url_for('forum.posts'))

