""":mod:`langdev.objsimplify` --- Object simplifier for generic serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import types
import collections
import langdev.util.visitor
import langdev.user


def simplify(value, identifier_map, type_map={}, url_map=None, user=None,
             **extra):
    """Simplifies a given ``value``.
    
    :param value: an object to simplify
    :param identifier_map: a map function that normalizes multi-word
                           identifiers
    :type identifier_map: callable object
    :param type_map: a type to mapping function dictionary
    :type type_map: :class:`dict`
    :param url_map: a map function that returns an url of a given ``value``
                    object. by default, it is a constant function that just
                    returns ``None``, so simplified dictionaries have no url
                    data
    :type url_map: callable object
    :param user: an user object for signing
    :type user: :class:`langdev.user.User`

    """
    options = dict(extra)
    options.update({'identifier_map': identifier_map,
                    'type_map': type_map,
                    'url_map': url_map,
                    'user': user})
    if type(value) in transform:
        d = transform(value, **options)
    elif hasattr(value, '__iter__'):
        d = transform[collections.Iterable](value, **options)
    else:
        d = value
    try:
        mapf = type_map[type(d)]
    except KeyError:
        return d
    return mapf(d)


def under_scores(identifier):
    '''Concatenates words of the ``identifier`` by underscore (``'_'``).

    .. sourcecode:: pycon

       >>> under_scores('key name')
       'key_name'
       >>> under_scores('encode URL')
       'encode_url'

    .. note::

       Use this function for :func:`simplify()` function's ``identifier_map``
       option.

    '''
    return '_'.join(identifier.split()).lower()


def PascalCase(identifier):
    '''Makes the ``identifier`` PascalCase.

    .. sourcecode:: pycon

       >>> PascalCase('key name')
       'KeyName'
       >>> PascalCase('encode URL')
       'EncodeURL'

    .. note::

       Use this function for :func:`simplify()` function's ``identifier_map``
       option.

    '''
    return ''.join(word[0].upper() + word[1:] for word in identifier.split())


def camelCase(identifier):
    '''Makes the ``identifier`` camelCase.

    .. sourcecode:: pycon

       >>> camelCase('key name')
       'keyName'
       >>> camelCase('encode URL')
       'encodeUrl'
       >>> camelCase('URL encoder')
       'urlEncoder'

    .. note::

       Use this function for :func:`simplify()` function's ``identifier_map``
       option.

    '''
    words = identifier.split()
    first = words[0].lower()
    words = [word.capitalize() for word in words[1:]]
    words.insert(0, first)
    return ''.join(words)


#: .. warning:: Internal use only. Use :func:`simplify` instead.
#:
#: The function that really implements simplification per types, without
#: :func:`simplify()`'s ``type_map`` option.
#:
#: :param value: an object to simplify
#: :param \*\*options: extra options
transform = langdev.util.visitor.Visitor('transform')


@transform.visit(collections.Iterable)
@transform.visit(list)
def transform(value, **options):
    return [simplify(v, **options) for v in value]


@transform.visit(langdev.user.User)
def transform(value, **options):
    idmap = options['identifier_map']
    d = {idmap('id'): simplify(value.id, **options),
         idmap('login'): simplify(value.login, **options),
         idmap('name'): simplify(value.name, **options),
         idmap('url'): simplify(value.url, **options),
         idmap('created at'): simplify(value.created_at, **options)}
    if options['user'] == value:
        d[idmap('email')] = simplify(value.email, **options)
    return d

