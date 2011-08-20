""":mod:`langdev.web` --- LangDev web services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LangDev uses Flask_ as framework for web frontend. It depends on Werkzeug_
and Jinja2_ also.

.. seealso::

   Module :mod:`langdev.web.home`
      Website home.

   Module :mod:`langdev.web.user`
      User authentications, personal pages, and so on.

   Module :mod:`langdev.web.forum`
      Forum post pages and comments.

   Module :mod:`langdev.web.thirdparty`
      Third-party applications.

   Module :mod:`langdev.web.pager`
      Pager for long length web application.

   Module :mod:`langdev.web.serializers`
      Serializers for various content types.

   Module :mod:`langdev.web.wsgi`
      Custom WSGI middlewares for LangDev web application.


.. _Flask: http://flask.pocoo.org/
.. _Werkzeug: http://werkzeug.pocoo.org/
.. _Jinja2: http://jinja.pocoo.org/

.. attribute:: flask.g.session

   (:class:`langdev.orm.Session`) The global variable that stores the
   SQLAlchemy session.

.. attribute:: flask.g.database_engine

   (:class:`sqlalchemy.engine.base.Engine`) The global variable that stores
   SQLAlchemy dtabase engine.

"""
import os.path
import flask
import flask.globals
import flaskext.mail
import werkzeug
import jinja2
import sqlalchemy
import langdev.orm


#: The :class:`dict` of modules to be registered by default.
#: Keys are import names in string, and values are keyword arguments for
#: :meth:`flask.Flask.register_module()` method. ::
#:
#:     modules = {'module.name:var': {'url_prefix': '/path'},
#:                'module.name2:var2': {}}
#:
#: It can be extended by ``MODULES`` configuration also::
#:
#:     MODULES = {'module.name:var': {}}
#:
#: .. seealso::
#:
#:    Function :func:`werkzeug.utils.import_string()`
#:       The function that imports an object based on a string, provided by
#:       Werkzeug_.
#:
#:    Flask --- :ref:`working-with-modules`
#:       Flask_ provides 'module' facilities for large applications.
#:
#: .. _Werkzeug: http://werkzeug.pocoo.org/
#: .. _Flask: http://flask.pocoo.org/
modules = {'langdev.web.home:home': {},
           'langdev.web.user:user': {'url_prefix': '/users'},
           'langdev.web.forum:forum': {'url_prefix': '/posts'},
           'langdev.web.thirdparty:thirdparty': {'url_prefix': '/apps'}}

#: The list of WSGI middlewares to hook in. Its elements are import names in
#: string. ::
#:
#:     wsgi_middlewares = ['langdev.web.wsgi:MethodRewriteMiddleware']
#:
#: It can be extended by ``WSGI_MIDDLEWARES`` configuration as well. ::
#:
#:     WSGI_MIDDLEWARES = ['werkzeug.contrib.fixers.ProxyFix']
#:
#: .. seealso::
#:
#:    Function :func:`werkzeug.utils.import_string()`
#:       The function that imports an object based on a string, provided by
#:       Werkzeug_.
#:
#:    Module :mod:`langdev.web.wsgi`
#:       Custom WSGI middlewares for LangDev web application.
#:
#:    Flask --- `Hooking in WSGI Middlewares`__
#:       Flask_ provides a way to hook in WSGI middlewares.
#:
#: __ http://flask.pocoo.org/docs/quickstart/#hooking-in-wsgi-middlewares
wsgi_middlewares = ['langdev.web.wsgi:MethodRewriteMiddleware']

#: Similar to :attr:`flask.Flask.before_request_funcs` attribute.
#: It is for lazy loading of global :attr:`~flask.Flask.before_request_funcs`
#: list.
before_request_funcs = []

#: Similar to :attr:`flask.Flask.after_request_funcs` attribute.
#: It is for lazy loading of global :attr:`~flask.Flask.after_request_funcs`
#: list.
after_request_funcs = []

# Similar to :attr:`flask.Flask.error_handlers` attribute.
#: It is for lazy loading of global :attr:`~flask.Flask.error_handlers` list.
error_handlers = {}

#: Internal storage dictionary for :func:`template_filter()` decorator.
template_filters = {}

#: The :class:`dict` of serializers for content types.
#: Keys are MIME types like :mimetype:`application/json`, and values are
#: functions that encode a value into the paired type, or a string which is
#: a postfix of the template filename e.g. ``'.html'``, ``'.xml'``. If value
#: is a string that doesn't start with period (``.``), it will be interpreted
#: as import name. ::
#:
#:     content_types = {'application/json': json.dumps,
#:                      'text/yaml': 'langdev.web.serializers:yaml',
#:                      'text/html': '.html',
#:                      'text/xml': '.xml'}
#:
#: .. seealso::
#:
#:    Function :func:`render()`
#:       The generic content type version of :func:`flask.render_template()`.
#:
#:    Function :func:`werkzeug.utils.import_string()`
#:       The function that imports an object based on a string, provided by
#:       Werkzeug_.
#:
#: .. _Werkzeug: http://werkzeug.pocoo.org/
content_types = {'text/html': '.html', 'application/xhtml+xml': '.html',
                 'text/xml': '.xml',
                 'application/json': 'langdev.web.serializers:json',
                 'application/plist+xml': 'langdev.web.serializers:plist',
                 'application/x-plist': 'langdev.web.serializers:plist'}

#: The default content type (MIME type) that is used for :mimetype:`*/*`.
default_content_type = 'text/html'


def create_app(modifier=None, config_filename=None):
    """An application factory. It sets up the application then returns
    the application. ::

        app = create_app(config_filename='prod.cfg')

    Instead you pass an argument ``config_filename``, it can be used as
    decorator-style as well::

        @create_app
        def app(app):
            app.debug = True
            app.config['MAGIC_NUMBER'] = 1234

    :param modifier: a function, for decorator-style use
    :type modifier: callable object
    :param config_filename: a configuration file name
    :type config_filename: :class:`basestring`
    :returns: a WSGI application
    :rtype: :class:`flask.Flask`

    """
    app = flask.Flask(__name__)
    if config_filename is not None:
        if isinstance(config_filename, basestring):
            config_path = os.path.abspath(os.path.join('.', config_filename))
            app.config.from_pyfile(config_path)
        else:
            raise TypeError('config_filename must be a filename string, not ' +
                            repr(config_filename))
    if modifier is not None:
        if callable(modifier):
            modifier(app)
        else:
            raise TypeError('modifier must be a callable object, not ' +
                            repr(modifier))
    mods = dict(modules)
    mods.update(app.config.get('MODULES', {}))
    for import_name, kwargs in modules.iteritems():
        modobj = werkzeug.utils.import_string(import_name)
        app.register_module(modobj, **(kwargs or {}))
    app.before_request_funcs.setdefault(None, []).extend(before_request_funcs)
    app.after_request_funcs.setdefault(None, []).extend(after_request_funcs)
    app.error_handlers.update(error_handlers)
    app.jinja_env.globals['method_for'] = method_for
    app.jinja_env.filters.update(template_filters)
    app.mail = flaskext.mail.Mail(app)
    middlewares = list(wsgi_middlewares)
    middlewares.extend(app.config.get('WSGI_MIDDLEWARES', []))
    for import_name in middlewares:
        app.wsgi_app = werkzeug.utils.import_string(import_name)(app.wsgi_app)
    return app


def before_request(function):
    """The decorator that registers ``function`` into
    :data:`before_request_funcs`.

    """
    before_request_funcs.append(function)
    return function


def after_request(function):
    """The decorator that registers ``function`` into
    :data:`after_request_funcs`.

    """
    after_request_funcs.append(function)
    return function


def errorhandler(code):
    """The decorator that registers a function into :data:`error_handlers`.
    ::

        @errorhandler(404)
        def not_found(error):
            return 'This page does not exist', 404

    :param code: an error status code to associate
    :type code: :class:`int`

    .. seealso:: Decorator Method :meth:`flask.Flask.errorhandler()`

    """
    def decorate(function):
        global error_handlers
        error_handlers[code] = function
        return function
    return decorate


def template_filter(name=None):
    """A decorator that is used to register custom template filter. You can
    specify a name for the filter, otherwise the function name will be used.
    Example::

        @template_filter
        def reverse(s):
            return s[::-1]

        @template_filter('order_by')
        def query_order_by(query, column):
            return query.order_by(column)

    :param name: the optional name of the filter, otherwise the function name
                 will be used
    :type name: :class:`basestring`

    """
    def decorate(f):
        template_filters[name or f.__name__] = f
        return f
    if callable(name):
        name = None
        return decorate(f)
    return decorate


def method_for(endpoint):
    """Gets the available method for ``endpoint``. It is useful for generating
    ``<form>`` tags.

    .. sourcecode:: jinja

       <form action="{{ url_for('endpoint') }}"
             method="{{ method_for('endpoint') }}">

    :param endpoint: an endpoint name to find the available method
    :type endpoint: :class:`basestring`
    :returns: an available method
    :rtype: :class:`basestring`

    """
    ctx = flask.globals._request_ctx_stack.top
    if '.' not in endpoint:
        mod = ctx.request.module
        if mod is not None:
            endpoint = mod + '.' + endpoint
    elif endpoint.startswith('.'):
        endpoint = endpoint[1:]
    methods = ctx.app.url_map._rules_by_endpoint[endpoint][0].methods
    try:
        return iter(methods.difference(['HEAD', 'OPTIONS'])).next()
    except StopIteration:
        pass


def render(template_name, value, **context):
    """The generic content type version of :func:`flask.render_template()`
    function. Unlike :func:`flask.render_template()`, it takes one more
    required parameter, ``value``, for generic serialization to JSON-like
    formats. And ``template_name`` doesn't include its postfix. ::

        render('user/profile', user, user=user)

    :param template_name: the name of the template to be rendered, but
                          postfix excluded
    :type template_name: :class:`basestring`
    :type value: the main object to be serialized into JSON-like formats
    :param \*\*context: the variables that should be available in the context
                        of the template

    .. seealso:: Constant :const:`content_types`
    .. todo:: Adding :mailheader:`Vary` header.

    """
    jinja_env = flask.current_app.jinja_env
    def _tpl_avail(postfix):
        try:
            jinja_env.get_template(template_name + postfix)
        except jinja2.TemplateNotFound:
            return False
        return True
    types = [mimetype for mimetype, f in content_types.iteritems()
                      if callable(f) or not f.startswith('.') or _tpl_avail(f)]
    # workaround for IE8. it sent wrong Accept header like below -_-
    # " Accept: image/pjpeg, image/pjpeg, image/gif, image/jpeg, */* "
    m = ((mime, q) for mime, q in flask.request.accept_mimetypes
                   if mime in types or mime == '*/*')
    accept_mimetypes = werkzeug.datastructures.MIMEAccept(m)
    if len(accept_mimetypes) == 1 and accept_mimetypes.values()[0] == '*/*':
        accept_mimetypes = [(default_content_type, 1)]
        accept_mimetypes = werkzeug.datastructures.MIMEAccept(accept_mimetypes)
    content_type = accept_mimetypes.best_match(types)
    try:
        serializer = content_types[content_type]
    except KeyError:
        flask.abort(406)
    if isinstance(serializer, basestring):
        if serializer.startswith('.'):
            template_name += serializer
            result = flask.render_template(template_name, **context)
            response = flask.Response(result, mimetype=content_type)
        else:
            serializer = werkzeug.utils.import_string(serializer)
    if callable(serializer):
        result = serializer(value)
        response = flask.Response(result, mimetype=content_type)
    response.headers['Vary'] = 'Accept'
    return response


def get_database_engine(config):
    """Gets SQLAlchemy :class:`~sqlalchemy.engine.base.Engine` object from the
    ``config``.

    :param config: the configuration that contains ``'DATABASE_URL'`` or
                   ``'ENGINE'``
    :type config: :class:`flask.Config`, :class:`dict`
    :returns: SQLAlchemy database engine
    :rtype: :class:`sqlalchemy.engine.base.Engine`

    .. seealso:: SQLAlchemy --- :ref:`engines_toplevel`

    """
    try:
        return config['ENGINE']
    except KeyError:
        pass
    url = config['DATABASE_URL']
    config['ENGINE'] = sqlalchemy.create_engine(url)
    return config['ENGINE']


@before_request
def define_session():
    """Sets the :attr:`g.session <flask.g.session>` and
    :attr:`g.database_engine <flask.g.database_engine>` global variables
    before every request.

    """
    flask.g.database_engine = get_database_engine(flask.current_app.config)
    flask.g.session = langdev.orm.Session(bind=flask.g.database_engine)


@template_filter('order_by')
def query_order_by(query, column):
    """Orders a ``query`` by ``column``.

    .. sourcecode:: jinja

       {% for post in user.posts|order_by('-created_at') %}
         - {{ post }}
       {% endfor %}

    :param column: a column name. if ``-`` character has prepended, it
                   becomes descending
    :type column: :class:`basestring`
    :returns: an ordered query
    :rtype: :class:`sqlalchemy.orm.query.Query`

    """
    cls = query._entities[0].type
    desc = False
    if column.startswith('-'):
        column = column[1:]
        desc = True
    column = getattr(cls, column)
    if desc:
        column = column.desc()
    return query.order_by(column)

