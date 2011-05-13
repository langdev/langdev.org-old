""":mod:`langdev` --- LangDev_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   This package is a namespace package. You can extend the :mod:`langdev`
   package in separated filesystem path. In order to do that, creates a
   folder named :file:`langdev`. Then, save the :file:`langdev/__init__.py`
   file of the following content::

       ''':mod:`langdev` --- LangDev
       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

       '''
       from pkgutil import extend_path
       __path__ = extend_path(__path__, __name__)

   Note that you must not make any variables/functions/class in the package,
   and creates modules like :mod:`langdev.foobar` under the package instead.

   .. seealso:: :pep:`382` --- Namespace Packages

.. _LangDev: http://langdev.org/

"""
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

