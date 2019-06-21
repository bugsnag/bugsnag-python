from bottle import route, run, app, static_file
import bugsnag

from bugsnag.wsgi.middleware import BugsnagMiddleware

bugsnag.configure(
    api_key='some-api-key',
)


@route('/')
def index():
    return static_file('index.html', root='.')


@route('/crash')
def crash():
    """Deliberately raises an unhandled error and crash the app.
    """
    raise Exception('SomethingBad')


@route('/handled')
def handle_zero_div():
    """Deliberately triggers a handled exception, and reports it to Bugsnag.
    """
    try:
        x = 1/0
    except Exception as e:
        bugsnag.notify(e)

    return ('The app hasn\'t crashed, but check https://app.bugsnag.com ' +
            'to view notifications')


app = app()
app.catchall = False
wrapped_app = BugsnagMiddleware(app)
run(app=wrapped_app, host='localhost', port=8080, debug=True)
