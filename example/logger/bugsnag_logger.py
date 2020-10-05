# www.bugsnag.com
# https://github.com/bugsnag/bugsnag-python/tree/master/example/logger
#
# this example app demonstrates some of the basic syntax to get Bugsnag error
# reporting configured in your Python code by integrating with a logger.
# ***********************************************************

import bugsnag
import logging
from bugsnag.handlers import BugsnagHandler


# Initialize Bugsnag to begin tracking errors. Only an api key is required, but
# here are some other helpful configuration details:
bugsnag.configure(
    # get your own api key at bugsnag.com
    api_key='YOUR_API_KEY_HERE',
    # if you track deploys or session rates, make sure to set the correct
    # version.
    app_version='1.2.3',
    # By default, requests are sent asynchronously. If you would like to block
    # until the request is done, you can set to false
    asynchronous=False,
    # Defaults to false, this allows you to log each session which will be used
    # to calculate crash rates in your dashboard for each release.
    auto_capture_sessions=True,
    # Sets which exception classes should never be sent to Bugsnag.
    ignore_classes=['Http404', 'DontCare'],
    # Defines the release stage for all events that occur in this app.
    release_stage='development',
    # Defines which release stages bugsnag should report. e.g. ignore staging
    # errors.
    notify_release_stages=['development', 'production'],
    # Any param key that contains one of these strings will be filtered out of
    # all error reports.
    params_filters=["credit_card_number", "password", "ssn"],
    # We mark stacktrace lines as inProject if they come from files inside
    # root:
    # project_root = "/path/to/your/app",
    # Useful if you are wrapping bugsnag.notify() in with your own library, to
    # ensure errors group properly.
    # traceback_exclude_module = [myapp.custom_logging],
)

# Create a logger
logger = logging.getLogger("test.logger")

# Create a Bugsnag handler.
# Optionally, add 'extra_fields' which will attach metadata to every Bugsnag
# report. The values should be attributes to pull off each log record.
handler = BugsnagHandler(extra_fields={"logger": ["__repr__"]})

# Define which level of log you want to report to Bugsnag. Here, warning &
# above.
handler.setLevel(logging.WARNING)

# Attach the Bugsnag handler to your logger.
logger.addHandler(handler)


# You can define a callback function which, when attached to your Bugsnag
# client, will run right before each and every report is sent to the api.  Here
# you can evaluate and modify the report data.
def callback(notification):
    """
    This callback will evaluate and modify every exception report, handled and
    unhandled, that occurs within the app, right before it is sent to Bugsnag.
    """
    # adding user info and metadata to every report:
    notification.user = {
        # in your app, you can pull these details from session.
        'name': 'Alan Turing',
        'email': 'turing@code.net',
        'id': '1234567890',
    }

    notification.add_tab('company', {'name': 'Stark Industries'})

    # The callback will evaluate all exceptions, but in this example only
    # 'SpecificError' class errors will have the below data added to their
    # error reports.
    if notification.exception.__class__.__name__ == 'SpecificError':
        notification.add_tab(
            'Diagnostics',
            {
                'message': 'Houston, we have a problem',
                'status': 200,
                'password': 'password1',  # this will be filtered
            },
        )
    # note that if you return false from the callback, this will cancel the
    # entire error report.


# Add callbacks for custom exception handling
def use_custom_exception_data(report):
    """
    If custom exception data is provided, replaces the report's default
    exception data with it, overriding the class and message seen on the
    Bugsnag dashboard. This attaches to the bugsnag.before_notify().
    """
    if 'custom' in report.metadata:
        exception = report.metadata['custom'].pop('custom exception', None)
        if exception is not None:
            report.exception = exception


def customize_exception_formatting(record, options):
    """
    Caches exception data based on the log record. This is a trivial example,
    though there could be custom log record properties which are more useful
    than than the generated error class and message.  This attaches to the log
    handler.
    """
    if record.exc_info is None:
        exc_type = type("MyCustomException", (Exception,), {})
        exception = exc_type(record.getMessage())
        exception.__module__ = None
        options['custom exception'] = exception


def set_unhandled_from_record(record, options):
    """
    Overwrites the default value of Bugsnag's 'unhandled' when a log is a level
    of ERROR or higher.
    """
    if record.levelno >= logging.ERROR:
        options['unhandled'] = True
        options['severity_reason'] = {'type': 'unhandledException'}


# attach your callbacks to Bugsnag. Important to attach AFTER 'addHandler'
# above, so that the function will have full access to the exception data.
bugsnag.before_notify(use_custom_exception_data)
bugsnag.before_notify(callback)

# Also can attach callbacks to the handler itself:
handler.add_callback(set_unhandled_from_record)
handler.add_callback(customize_exception_formatting)


# This file has configured your Bugsnag client and attached it to your logger.
# Now you can import the logger to any other python files in your app, and all
# exceptions & logs will be reported to your Bugsnag dashboard.
