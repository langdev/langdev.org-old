""":mod:`langdev.web.wsgi` --- Custom WSGI middlewares
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import flask
import werkzeug.urls


class MethodRewriteMiddleware(object):
    """The WSGI middleware that overrides HTTP methods for old browsers.
    HTML4 and XHTML only specify ``POST`` and ``GET`` as HTTP methods that
    ``<form>`` elements can use. HTTP itself however supports a wider range
    of methods, and it makes sense to support them on ther server.
    
    If you however want to make a form submission with ``PUT`` for instance,
    and you are using a client that does not support it, you can override it
    by using this middleware and appending ``?__method__=PUT`` to the
    ``<form>`` ``action``.

    .. sourcecode:: html

       <form action="?__method__=put" method="post">
         ...
       </form>

    :param application: WSGI application to wrap
    :type application: callable object

    .. seealso:: Flask --- `Overriding HTTP Methods for old browsers`__

    __ http://flask.pocoo.org/snippets/38/

    """

    __slots__ = 'application',

    def __init__(self, application):
        if not callable(application):
            raise TypeError('application must be callable, but {0!r} is not '
                            'callable'.format(application))
        self.application = application

    def __call__(self, environ, start_response):
        if (environ['REQUEST_METHOD'].upper() == 'POST' and
            '__method__' in environ.get('QUERY_STRING', '')):
            args = werkzeug.urls.url_decode(environ['QUERY_STRING'])
            method = args.get('__method__', '').upper()
            if method in ('HEAD', 'GET', 'POST', 'PUT', 'DELETE'):
                environ['REQUEST_METHOD'] = method
        return self.application(environ, start_response)


class HostRewriteMiddleware(object):
    """A WSGI middleware that overwrites every request's :mailheader:`Host`
    header (that is, ``HTTP_HOST`` environment) to the specific ``host``
    name. It is useful when WSGI server is running under proxy server.

    :param application: WSGI application to wrap
    :type application: callable object, :class:`flask.Flask`
    :param host: a host name to rewrite. if not present, ``HOST_REWRITE``
                 configuration may be used (only when ``application`` is a
                 :class:`flask.Flask` instance)
    :type host: :class:`basestring`

    """

    __slots__ = 'application', 'host'

    def __init__(self, application, host=None, config_name='HOST_REWRITE'):
        if isinstance(application, flask.Flask):
            self.application = application.wsgi_app
            self.host = host or application.config.get(config_name)
        elif not callable(application):
            raise TypeError('application must be callable, but {0!r} is not '
                            'callable'.format(application))
        else:
            self.application = application
            self.host = host

    def __call__(self, environ, start_response):
        if self.host:
            environ = dict(environ)
            environ['HTTP_HOST'] = self.host
        return self.application(environ, start_response)

