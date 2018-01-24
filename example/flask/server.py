from flask import Flask, request, render_template
import bugsnag

# Import platform specific Bugsnag features
from bugsnag.flask import handle_exceptions

app = Flask(__name__)

# Initialize Bugsnag to begin tracking errors. Only an api key is required, but here are some other helpful configuration details:
bugsnag.configure(
    # get your own api key at bugsnag.com
    api_key = '03c1b987da2ed0df8795cc4968b76185',

    # if you track deploys, make sure to set the correct version.
    app_version = '1.2.3',

    # Defaults to false, this allows you to log each session whcih will be sued to calculate crash rates in your dashboard for each release.
    auto_capture_sessions = True,

    # Sets which exception classes should never be sent to Bugsnag.
    ignore_classes = ['Http404', 'DontCare'],

    # defines the release stage for all events that occur in this app.
    release_stage = 'development',

    # defines which release stages bugsnag should report. e.g. ignore staging errors.
    notify_release_stages = [ 'development', 'production'],

    # any param key that contains one of these strings will be removed fomr all erroro reports.
    params_filters = ["credit_card_number", "password", "ssn"],

    # We mark stacktrace lines as inProject if they come from files inside:
    # project_root = "/path/to/your/app",

    # By default, we send a few lines of source code to Bugsnag along with the exception report. If you want to stop this from happening, you can set to False.
    send_code = True,
)

# You can define a callback function which, when attached to to your Bugsnag client, will run right before each anad every report is sent to our api.  Here you can evaluate and modify the report data.
def callback(notification):
    # USER
    # meta_data
    print "notification.message" + notification.options.message
    if notification.context == 'WHAAAAAAAT':

        notification.add_tab('Diagnostics', {
            'message': 'Flask demo: Everything is fine',
            'status': 200,
            'password': 'password1' # this will be removed by your param_filters.
        })
    # note that if you return false from the callback, this will cancel the entire error report.

# attach your callback to Bugsnag:
bugsnag.before_notify(callback)

# Attach Bugsnag to flasks exception handler
handle_exceptions(app)

@app.route('/')
def index():
    return render_template('index.html')

# Should cause a KeyError to be caught by the bugsnag exception handler
@app.route('/crashdict')
def crashdict():
    customheader = request.headers['my-custom-header']
    return 'Received your header: ' + customheader

# Will crash but attach diagnostic data through a callback function before reporting the error
@app.route('/crashcallback')
def crashcallback():
    raise(Exception('WHAAAAAAAT'))
    # this error will meet the conditional defined in the global before_notify above, which will then attach diagnostic data to the report.

# Will notify Bugsnag of an exception manually, which can be used to notify Bugsnag of handled errors
@app.route('/notify')
def notify():
    bugsnag.notify(Exception('Flask demo: Manual notification'))
    return 'The app hasn\'t crashed, but check <a href=\"bugsnag.com\">bugsnag.com</a> to view notifications'

# Will notify Bugsnag of an exception, with some metadata attached for better debugging
@app.route('/notifywithmetadata')
def notifywithmetadata():
    bugsnag.notify(
        Exception('Flask demo: Manual notification with metadata'),
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

# Will notify Bugsnag of an exception, and include a context included for grouping
@app.route('/notifywithcontext')
def notifywithcontext():
    bugsnag.notify(
        Exception('Flask demo: Manual notification with context'),
        context = 'notifywithcontext'
    )
    return 'The context was changed to notifywithcontext for better grouping'

# Will notify Bugsnag of an exception, with a defined severity for different handling
@app.route('/notifywithseverity')
def notifywithseverity():
    bugsnag.notify(
        Exception('Flask demo: Manual notificaiton with severity'),
        severity = 'info',
    )
    return 'The severity was set to info, check <a href=\"bugsnag.com\">bugsnag.com</a> to see the difference'


if __name__ == '__main__':
    app.run(port=3000)
