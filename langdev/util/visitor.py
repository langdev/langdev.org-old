""":mod:`langdev.util.visitor` --- Simple visitor pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides a simple straightforward implementation of visitor
pattern.

.. sourcecode:: pycon

   >>> compile = Visitor('compile')
   >>> @compile.visit(int)
   ... @compile.visit(long)
   ... def compile(value):
   ...     return str(value)
   ...
   >>> @compile.visit(basestring)
   ... def compile(value):
   ...     return "'{0}'".format(value)
   ...
   >>> @compile.visit(unicode)
   ... def compile(value):
   ...     return 'u' + compile[basestring](value)
   ...
   >>> @compile.visit(list)
   ... def compile(value):
   ...     return '[{0}]'.format(', '.join(compile(v) for v in value))
   ...
   >>> compile([1, 2, '3', u'4', [5, 6]])
   '[1, 2, '3', u'4', [5, 6]]'

"""
import types


class Visitor(object):
    """Visitor function object.

    .. sourcecode:: pycon

       >>> compile = Visitor('compile')
       >>> compile  # doctest: +ELLIPSIS
       <styleshare.util.visitor.Visitor 'compile' at ...>
       >>> compile.__name__
       'compile'

    :param name: the name of the visitor function
    :type name: :class:`str`
    :param argument: the argument position (in case of integer) or
                     keyword (in case of string) to visit. the first argument
                     by default
    :type argument: :class:`int`, :class:`long`, :class:`str`

    .. attribute:: functions

       Registered functions by types in :class:`dict`.

    .. attribute:: argument

       The argument position (in case of :class:`int`) or keyword (in case
       of :class:`str`) to visit.

    .. attribute:: latest_added_function

       The latest added function. May be ``None``.

    .. attribute:: __name__

       The name of the visitor function.

    """

    __slots__ = '__name__', 'argument', 'functions', 'latest_added_function'

    def __init__(self, name, argument=0):
        self.__name__ = name
        self.argument = argument
        self.functions = {}
        self.latest_added_function = None

    def visit(self, type):
        """Returns a decorator to register a function.

        .. sourcecode:: pycon

           >>> compile = Visitor('compile')
           >>> @compile.visit(int)
           ... @compile.visit(long)
           ... def compile(value):
           ...     return 'int: {0}'.format(value)
           ...

        :param type: a type to connect with a function
        :type type: :class:`types.TypeType`
        :returns: a :class:`VisitorDecorator` instance
        :rtype: :class:`VisitorDecorator`

        """
        return VisitorDecorator(self, type)

    def __contains__(self, type):
        if isinstance(type, types.TypeType):
            for cls in type.mro():
                if cls in self.functions:
                    return True
        return type in self.functions

    def __getitem__(self, type):
        if isinstance(type, types.TypeType):
            for cls in type.mro():
                try:
                    return self.functions[cls]
                except KeyError as e:
                    pass
        return self.functions[type]

    def __setitem__(self, type, function):
        self.functions[type] = function
        self.latest_added_function = function

    def __call__(self, *args, **kwargs):
        vargs = args if isinstance(self.argument, (int, long)) else kwargs
        try:
            f = self[type(vargs[self.argument])]
        except KeyError:
            raise TypeError('{0!r} does not match for the function '
                            '{1!r}'.format(args[0], self.__name__))
        return f(*args, **kwargs)

    def __repr__(self):
        return '<{0}.{1} {2!r} at {3:x}>'.format(__name__,
                                                 type(self).__name__,
                                                 self.__name__, id(self))


class VisitorDecorator(object):
    """Decorator function object to register a function to :class:`Visitor`.
    Internally used.

    :param visitor: a :class:`Visitor` instance
    :type visitor: :class:`Visitor`
    :param type: a type object
    :type type: :class:`types.TypeType`

    .. attribute:: visitor

       The :class:`Visitor` instance.

    .. attribute:: type

       The type object, :class:`types.TypeType` instance.

    """

    __slots__ = 'visitor', 'type'

    def __init__(self, visitor, type):
        if not isinstance(visitor, Visitor):
            raise TypeError('visitor must be a comedy.visitor.Visitor '
                            'instance, not ' + repr(visitor))
        elif not isinstance(type, types.TypeType):
            raise TypeError('type must be a types.TypeType instance, not ' +
                            repr(type))
        self.visitor = visitor
        self.type = type

    def __call__(self, function):
        if function is self.visitor:
            function = self.visitor.latest_added_function
        self.visitor[self.type] = function
        return self.visitor


class TypeVisitor(Visitor):
    """Same as :class:`Visitor`, except it deals with type instead of
    instance.

    .. sourcecode:: pycon

       >>> compile = TypeVisitor('compile')
       >>> compile  # doctest: +ELLIPSIS
       <styleshare.util.visitor.TypeVisitor 'compile' at ...>
       >>> compile.__name__
       'compile'

    """

    def __call__(self, *args, **kwargs):
        vargs = args if isinstance(self.argument, (int, long)) else kwargs
        try:
            f = self[vargs[self.argument]]
        except KeyError:
            raise TypeError('{0!r} does not match for the function '
                            '{1!r}'.format(args[0], self.__name__))
        return f(*args, **kwargs)

