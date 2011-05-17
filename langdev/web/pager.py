""":mod:`langdev.web.pager` --- Pager for long length web application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the pager like following look::

    [1]  2  3  4  5  6  7  8  9  10  ...  123
    1  2  3  [4]  5  6  7  8  9  10  ...  123
    1  ...  53  54  55  56  57  [58]  59  60  61  62  ...  123
    1  ...  113  114  115  116  117  118  [119]  120  121  122  123
    1  ...  113  114  115  116  117  118  119  120  121  122  [123]


It can be used like following code with Jinja_:

.. sourcecode:: jinja

   <ul class="pager">
     {% for flag, page in pager %}
     <li class="{{ flag is number and '' or flag }}">
       <a href="/?page={{ page }}">{{ page }}</a>
     </li>
     {% endfor %}
   </ul>

.. _Jinja: http://jinja2.pocoo.org/

"""
import math


__all__ = ['Pager', 'pager']


class Pager(object):
    """:class:`Pager` class that is iterable. :class:`Pager` instances can be
    looped with ``for`` statements.

    The length represents a maximum number of pages.

    .. sourcecode:: pycon

       >>> list(Pager(7))
       [('selected', 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7)]

    The selected_page represents a currently selected page number. Its default
    value is just ``1``.

    .. sourcecode:: pycon

       >>> list(Pager(7, selected_page=5))
       [(1, 1), (2, 2), (3, 3), (4, 4), ('selected', 5), (6, 6), (7, 7)]
       >>> list(Pager(7, selected_page=7))
       [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), ('selected', 7)]

    Last, the width represents how many page numbers are shown at once. First
    and last page numbers are excluded in the width.

    .. sourcecode:: pycon

       >>> list(Pager(8, 4, width=5))
       [(1, 1), (2, 2), (3, 3), ('selected', 4), (5, 5), ('last', 8)]

    The form of sequence is ``[(flag_or_page, page), ...]``. In
    ``(flag, page)`` pair, the flag can be :const:`Pager.FIRST` (``"first"``),
    :const:`Page.LAST` (``"last"``), :const:`Page.SELECTED` (``"selected"``) or
    ordinal page number.

    .. sourcecode:: pycon

       >>> list(Pager(100, 100, width=5))  # doctest: +NORMALIZE_WHITESPACE
       [('first', 1), (96, 96), (97, 97), (98, 98), (99, 99),
        ('selected', 100)]
       >>> list(Pager(100, 1, width=5))
       [('selected', 1), (2, 2), (3, 3), (4, 4), (5, 5), ('last', 100)]
       >>> list(Pager(100, 50, width=5))  # doctest: +NORMALIZE_WHITESPACE
       [('first', 1), (48, 48), (49, 49), ('selected', 50), (51, 51),
        (52, 52), ('last', 100)]

    Pager is iterable, so it can be used in ``for`` loop.

    .. sourcecode:: pycon

       >>> for typ, page in Pager(100, 50, width=5):
       ...   if typ == Pager.LAST:
       ...     print "...",
       ...   if typ == Pager.SELECTED:
       ...     print "[{0}]".format(page),
       ...   else:
       ...     print page,
       ...   if typ == Pager.FIRST:
       ...     print "...",
       1 ... 48 49 [50] 51 52 ... 100

    :param length: total length of pages
    :type length: :class:`int`, :class:`long`
    :param selected_page: currently selected page number. default value is ``1``
    :type selected_page: :class:`int`, :class:`long`
    :param width: pager's width. default value is :const:`DEFAULT_WIDTH`
    :type width: :class:`int`, :class:`long`

    .. data:: DEFAULT_WIDTH

       Default width which is exactly ``10``.

    .. data:: FIRST

       Flag value which is exactly ``"first"`` for first page.

    .. data:: LAST

       Flag value which is exactly ``"last"`` for last page.

    .. data:: SELECTED

       Flag value which is exactly ``"selected"`` for selected page.

    """

    DEFAULT_WIDTH = 10
    FIRST = 'first'
    LAST = 'last'
    SELECTED = 'selected'

    __slots__ = 'length', 'selected_page', 'width'

    def __init__(self, length, selected_page=1, width=DEFAULT_WIDTH):
        self.length = int(length)
        self.selected_page = int(selected_page)
        self.width = int(width)

    def __iter__(self):
        half = self.width / 2
        if self.length > self.width and self.selected_page > half + 2:
            yield self.FIRST, 1
            i = self.length - self.width + 1 \
                if self.selected_page + half >= self.length \
                else self.selected_page - half
        else:
            i = 1
        to = min(i + self.width, 1 + self.length)
        for i in xrange(i, to):
            yield self.SELECTED if i == self.selected_page else i, i
        if max(self.selected_page, to) <= self.length:
            yield self.LAST, self.length

    def __repr__(self):
        cls = type(self)
        args = self.length, self.selected_page, self.width
        return '{0}.{1}{2!r}'.format(cls.__module__, cls.__name__, args)


pager = Pager

