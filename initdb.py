import sys
import sqlalchemy
import langdev.orm
import langdev.user


if len(sys.argv) < 2:
    print>>sys.stderr, 'usage: initdb.py database-url'
    print>>sys.stderr, 'see also http://.sqlalchemy.org/docs/core/engines' \
                       '.html#database-urls'
    raise SystemExit()

database_url = sys.argv[1]
engine = sqlalchemy.create_engine(database_url)
langdev.orm.Base.metadata.create_all(engine)
