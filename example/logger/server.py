# www.bugsnag.com
# https://github.com/bugsnag/bugsnag-python/tree/master/example/logger
#
# this example app demonstrates some of the basic syntax to get Bugsnag error reporting configured in your Python code by integrating with a logger.
# ***********************************************************

import bugsnag
import logging
from bugsnag.handlers import BugsnagHandler


# Initialize Bugsnag to begin tracking errors. Only an api key is required, but here are some other helpful configuration details:
bugsnag.configure(

    # get your own api key at bugsnag.com
    api_key = '03c1b987da2ed0df8795cc4968b76185',

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

# Create a logger
logger = logging.getLogger("test.logger")

# Add a Bugsnag handler
handler = BugsnagHandler()
handler.setLevel(logging.WARNING)
logger.addHandler(handler)

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

# # Add callbacks for custom exception handling
# def use_custom_exception_data(report):
#   if 'custom' in report.meta_data:
#     exception = report.meta_data['custom'].pop('custom exception', None)
#   if exception is not None:
#     report.exception = exception


def customize_exception_formatting(record, options):
  if record.exc_info is None:
    exc_type = type("MyCustomException", (Exception,), {})
    exception = exc_type(record.getMessage())
    exception.__module__ = None
    options['custom exception'] = exception


def set_unhandled_from_record(record, options):
  if record.levelno >= logging.ERROR:
    options['unhandled'] = True
    options['severity_reason'] = {'type': 'unhandledException'}

# attach your callback to Bugsnag. Important to attach AFTER 'handle_exceptions(app)' above, so that the function will have full access to the exception data.
bugsnag.before_notify(callback)
handler.add_callback(set_unhandled_from_record)
handler.add_callback(customize_exception_formatting)


if __name__ == '__main__':
    logger.info("This is purely informational.")  # will not report to Bugsnag because it is below handler.setLevel
    logger.warn("This is a warning!")
    logger.error("I forgot my lunch at home")
    logger.critical(Exception("The system is down!"))
    # x = 1/0









#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# @app.route('/crashdict')
# def crashdict():
#     """Deliberately triggers an unhandled KeyError to be reported by the bugsnag exception handler, and crash the app.
#     """
#     customheader = request.headers['my-custom-header']
#     return 'Received your header: ' + customheader
#
#
# @app.route('/crashcallback')
# def crashcallback():
#     """Deliberately raises an unhandled error which will have diagnostic data attached by the global callback function, and crash the app.
#     """
#     raise(Exception('SomethingBad'))
#
#
# @app.route('/handled')
# def notify():
#     """Deliberately triggers a handled exception, and reports it to Bugsnag.
#     """
#     try:
#         x = 1/0
#     except ZeroDivisionError:
#         bugsnag.notify(ZeroDivisionError('Flask demo: To infinity... and beyond!'))
#
#     return 'The app hasn\'t crashed, but check <a href=\"bugsnag.com\">bugsnag.com</a> to view notifications'
#
#
# @app.route('/notifywithmetadata')
# def notifywithmetadata():
#     """Manually notifies Bugsnag of a handled exception, with some metadata locally attached.
#     """
#     bugsnag.notify(
#         Exception('Flask demo: Manual notification with metadata'),
#         # this app adds some metadata globally, but you can also attach specfic details to a particular
#         meta_data = {
#             'Request info': {
#                 'route': 'notifywithmetadata',
#                 'headers': request.headers
#             },
#             'Resolve info': {
#                 'status': 200,
#                 'message': 'Metadata has been added to this notification'
#             }
#         },
#     )
#     return ('Metadata was added to the notification, check <a href=\"bugsnag.com\">bugsnag.com</a> ' +
#         ' to view on the "Request info" and "Resolve info" tabs')
#
#
# @app.route('/notifywithcontext')
# def notifywithcontext():
#     """Notifies Bugsnag of a handled exception, which has a modified 'context' attribute for the purpose of improving how these exceptions will group together in the Bugsnag dashboard, and a severity attribute that has been modifed to overwrite the default level (warning).
#     """
#     bugsnag.notify(
#         Exception('Flask demo: Manual notification with context and severity'),
#         context = 'notifywithcontext',
#         severity = 'info'
#     )
#     return 'The context and severity were changed.'
#
#
#
