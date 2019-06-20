# www.bugsnag.com
# https://github.com/bugsnag/bugsnag-python/tree/master/example/flask
#
# this example app demonstrates some of the basic syntax to get Bugsnag error reporting configured in your Python Flask code.
# ***********************************************************

from flask import Flask, request, render_template
import bugsnag
# Import platform specific Bugsnag features
from bugsnag.flask import handle_exceptions

app = Flask(__name__)

# Initialize Bugsnag to begin tracking errors. Only an api key is required, but here are some other helpful configuration details:
bugsnag.configure(

    # get your own api key at bugsnag.com
    api_key = 'YOUR_API_KEY_HERE',

    # if you track deploys or session rates, make sure to set the correct version.
    app_version = '1.2.3',

    # By default, requests are sent asynchronously. If you would like to block until the request is done, you can set to false
    asynchronous = False,

    # Defaults to false, this allows you to log each session which will be used to calculate crash rates in your dashboard for each release.
    auto_capture_sessions = True,

    # Sets which exception classes should never be sent to Bugsnag.
    ignore_classes = ['Http404', 'DontCare'],

    # Defines the release stage for all events that occur in this app.
    release_stage = 'development',

    # Defines which release stages bugsnag should report. e.g. ignore staging errors.
    notify_release_stages = [ 'development', 'production'],

    # Any param key that contains one of these strings will be filtered out of all error reports.
    params_filters = ["credit_card_number", "password", "ssn"],

    # We mark stacktrace lines as inProject if they come from files inside root:
    # project_root = "/path/to/your/app",

    # Useful if you are wrapping bugsnag.notify() in with your own library, to ensure errors group properly.
    # traceback_exclude_module = [myapp.custom_logging],

)

# Attach Bugsnag to flask's exception handler
handle_exceptions(app)

# You can define a callback function which, when attached to to your Bugsnag client, will run right before each and every report is sent to the api.  Here you can evaluate and modify the report data.
def callback(notification):
    """This callback will evaluate and modify every exception report, handled and unhandled, that occurs within the app, right before it is sent to Bugsnag.
    """
    # adding user info and metadata to every report:
    notification.user = {
        # in your app, you can pull these details from session.
        'name': 'Alan Turing',
        'email': 'turing@code.net',
        'id': '1234567890'
    }

    notification.add_tab(
        'company', {
            'name': 'Stark Industries'
        }
    )

    if notification.context == 'GET /crashcallback':
        # The callback will evaluate all exceptions, but in this example only errors from @app.route('/crashcallback') will have the below data added to their error reports.
        notification.add_tab('Diagnostics', {
            'message': 'Flask demo: Everything is fine',
            'status': 200,
            'password': 'password1' # this will be filtered by your param_filters.
        })
    # note that if you return false from the callback, this will cancel the entire error report.

# attach your callback to Bugsnag. Important to attach AFTER 'handle_exceptions(app)' above, so that the function will have full access to the exception data.
bugsnag.before_notify(callback)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/crashdict')
def crashdict():
    """Deliberately triggers an unhandled KeyError to be reported by the bugsnag exception handler, and crash the app.
    """
    customheader = request.headers['my-custom-header']
    return 'Received your header: ' + customheader


@app.route('/crashcallback')
def crashcallback():
    """Deliberately raises an unhandled error which will have diagnostic data attached by the global callback function, and crash the app.
    """
    raise(Exception('SomethingBad'))


@app.route('/handled')
def handle_zero_div():
    """Deliberately triggers a handled exception, and reports it to Bugsnag.
    """
    try:
        x = 1/0
    except Exception as e:
        bugsnag.notify(e)

    return 'The app hasn\'t crashed, but check <a href=\"https://app.bugsnag.com\">app.bugsnag.com</a> to view notifications'

@app.route('/notifywithmetadata')
def notifywithmetadata():
    """Manually notifies Bugsnag of a handled exception, with some metadata locally attached.
    """
    bugsnag.notify(
        Exception('Flask demo: Manual notification with metadata'),
        # this app adds some metadata globally, but you can also attach specfic details to a particular exception
        meta_data = {
            'Request info': {
                'route': 'notifywithmetadata',
                'headers': request.headers
            },
            'Resolve info': {
                'status': 200,
                'message': 'Metadata has been added to this notification'
            }
        },
    )
    return ('Metadata was added to the notification, check <a href=\"bugsnag.com\">bugsnag.com</a> ' +
        ' to view on the "Request info" and "Resolve info" tabs')


@app.route('/notifywithcontext')
def notifywithcontext():
    """Notifies Bugsnag of a handled exception, which has a modified 'context' attribute for the purpose of improving how these exceptions will group together in the Bugsnag dashboard, and a severity attribute that has been modifed to overwrite the default level (warning).
    """
    bugsnag.notify(
        Exception('Flask demo: Manual notification with context and severity'),
        context = 'notifywithcontext',
        severity = 'info'
    )
    return 'The context and severity were changed.'


if __name__ == '__main__':
    app.run(port=3000)
