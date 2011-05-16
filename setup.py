import os
import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import distutils.util


def find_packages(where='.'):
    """Borrowed from `Distribute <http://packages.python.org/distribute/>`_."""
    out = []
    stack=[(distutils.util.convert_path(where), '')]
    while stack:
        where,prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if ('.' not in name and os.path.isdir(fn) and
                os.path.isfile(os.path.join(fn, '__init__.py'))):
                out.append(prefix+name); stack.append((fn, prefix + name + '.'))
    for pat in 'ez_setup', 'distribute_setup':
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item, pat)]
    return out


setup(name='LangDev',
      version='0.1',
      url='http://langdev.org/',
      author='Hong Minhee',
      author_email='minhee' '@' 'dahlia.kr',
      description='Programming language implementors and designers community.',
      packages=find_packages(),
      install_requires=['SQLAlchemy', 'Flask', 'Werkzeug', 'Jinja2',
                        'Flask-WTF', 'Flask-Script'],
      include_package_data=True,
      zip_safe=False,
      license='AGPLv3')

