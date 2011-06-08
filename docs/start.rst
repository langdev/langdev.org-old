
Getting started
===============

Setup
-----

LangDev source code is available at the `Mercurial repository
<https://bitbucket.org/dahlia/langdev>`_. Checkout this:

.. sourcecode:: bash

   $ hg clone https://bitbucket.org/dahlia/langdev
   $ cd langdev/
   langdev$

It depends on several Python library packages. You can resolve all of
dependencies at once like:

.. sourcecode:: bash

   langdev$ python setup.py develop

It also adds your working directory into Python site-packages as develepment
mode.

.. seealso::

   `Installing Python Modules <http://docs.python.org/install/index.html>`_
      This document describes the Python Distribution Utilities ("Distutils")
      from the end-user's point-of-view, describing how to extend the
      capabilities of a standard Python installation by building and
      installing third-party Python modules and extensions.

   `"Development Mode"
   <http://packages.python.org/distribute/setuptools.html#development-mode>`_
      Distribute (setuptools)'s development mode.

.. note::

   It probably is that virtualenv_ could be useful for your development.
   It isolates Python site-package environments from global site-packages.

   .. sourcecode:: bash

      $ virtualenv --distribute langdev-env
      $ cd langdev-env
      langdev-env$ source bin/activate
      (langdev-env)langdev-env$

   Packages that installed in the virtualenv don't belong to global
   site-packages. Instead, they are in :file:`langdev-env/site-packages/`
   (in the above example).

   .. seealso::

      virtualenv_
         A tool to create isolated Python environments.

   .. _virtualenv: http://www.virtualenv.org/en/latest/index.html


.. program:: mangage_langdev.py

Configuration file
------------------

If you checkout the source code, there might be :program:`manage_langdev.py`
program. It helps you to make a configuration, initialize a database,
or run a web server.

LangDev supports multiple instances, and instances' metadata that are stored
in the configuration file. From here, we assume that our configuration
filename is :file:`instance.cfg`. (Of course, there's no such file currently.)
You can name it freely like :file:`dev.cfg` or :file:`prod.cfg`.

You can pass a filename that doesn't exist into :option:`--config
<manage_langdev.py --config>` option, and the script will confirm would you
want to create a such configuration file.

.. sourcecode:: bash

   $ manage_langdev.py shell --config instance.cfg
   instance.cfg doesn't exist yet; would you create it? [y] 

There's some fields to be set like database URL:

**Database URL** (:data:`DATABASE_URL`)
   The database to be used. By default it uses SQLite with a database file
   (:file:`db.sqlite`) located in the current directory.

   .. sourcecode:: text

      Database URL [sqlite:////home/dahlia/Desktop/langdev-env/db.sqlite]:

   .. seealso:: SQLAlchemy --- `Database Urls
      <http://www.sqlalchemy.org/docs/core/engines.html#database-urls>`_

**Secret key for secure session** (:data:`SECRET_KEY`)
   The HMAC secret key. The default key is randomly generated, so skip this
   if you don't know about HMAC or secure session.

   .. sourcecode:: text

      Secret key for secure cookies [ab03199d87db101aa07fd18e3dc2599a]:

   .. seealso::

      Flask --- :ref:`sessions`
         Flask provdes client-side secure sessions.

      Class :class:`flask.session`
         The session object works pretty much like an ordinary dict,
         with the difference that it keeps track on modifications.
   
      :rfc:`2104` --- HMAC: Keyed-Hashing for Message Authentication
         This document describes HMAC, a mechanism for message authentication
         using cryptographic hash functions. HMAC can be used with any
         iterative cryptographic hash function, e.g., MD5, SHA-1, in
         combination with a secret shared key.  The cryptographic strength of
         HMAC depends on the properties of the underlying hash function.

.. seealso:: Flask --- :ref:`config`


Database initialization
-----------------------

What you have to do next is creating tables into your relational database.
There are to recommended relational databases:

SQLite_ 3+
   SQLite is a small and powerful file-based relational database.
   It is recommended for development-purpose.

PostgreSQL_ 8.3+
   PostgreSQL is a powerful object-relational database system.
   We recommend it for production-use.

You make a decision, and then, initialize the database via
:program:`manage_langdev.py initdb` command:

.. sourcecode:: bash

   $ manage_langdev.py initdb --config instance.cfg

No news is good news. It doesn't print anything unless errors happen.

.. note::

   If you would use SQLite_, the data file will be automatically created.
   But if you would use PostgreSQL_, the database to be used have to be
   created first. Create a database via the :program:`createdb` command
   PostgreSQL provides:

   .. sourcecode:: bash

      $ createdb -U postgres -E utf8 -T postgres langdev_db

.. _SQLite: http://www.sqlite.org/
.. _PostgreSQL: http://www.postgresql.org/


.. _web-server:

Web server
----------

We finished configuring an instance. Now we can run the development web server
from command line:

.. sourcecode:: bash

   $ manage_langdev.py runserver --config instance.cfg


How to serve on WSGI servers
----------------------------

.. note:: It explains advanced details. If you don't know about WSGI, skip
          this section and follow :ref:`web-server` section.

LangDev web application is WSGI-compliant, so it can be served on WSGI
servers. For example, in order to serve it on Meinheld_ server, make a script::

    import langdev.web
    import meinheld.server

    app = langdev.web.create_app(config_filename='instance.cfg')
    meinheld.server.listen(('0.0.0.0', 8080))
    meinheld.server.run(app)

Let's cut to the chase. :func:`langdev.web.create_app()` makes a WSGI
application and returns it. It takes a ``config_filename`` optionally
(and it have to be passed by keyword, not positional). And then, pass the
created WSGI application into your favorite WSGI server.

.. _Meinheld: http://meinheld.org/

