from bottle import route, run, app, static_file
import bugsnag

from bugsnag.wsgi.middleware import BugsnagMiddleware

bugsnag.configure(
    api_key='698ffb05632f0ffcad3ebd16383507fd',
)

@route('/')
def index():
    return static_file('index.html', root='.')

@route('/crash')
def crash():
    """Deliberately raises an unhandled error and crash the app.
    """
    raise(Exception('SomethingBad'))

@route('/handled')
def handled():
    try:
        x = 1/0
    except ZeroDivisionError:
        bugsnag.notify(ZeroDivisionError('Bottle demo: To infinity... and beyond!'))

    return 'The app hasn\'t crashed, but check <a href=\"bugsnag.com\">bugsnag.com</a> to view notifications'

app = app()
app.catchall = False
wrappedApp = BugsnagMiddleware(app)
run(app=wrappedApp, host='localhost', port=8080, debug=True)
