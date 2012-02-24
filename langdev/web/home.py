""":mod:`langdev.web.home` --- Website home
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Blueprint, redirect, url_for


#: Home blueprint.
#:
#: .. seealso:: Flask --- :ref:`flask:blueprints`
home = Blueprint('home', __name__)


@home.route('/')
def main():
    return redirect(url_for('forum.posts'))

