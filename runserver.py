import sys
import langdev.web


if len(sys.argv) < 2:
    print>>sys.stderr, 'usage:', sys.argv[0], 'config'
    raise SystemExit()

app = langdev.web.create_app(config_filename=sys.argv[1])
app.run(debug=True)

