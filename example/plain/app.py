# www.bugsnag.com
# https://github.com/bugsnag/bugsnag-python/tree/master/example/plain
#
# this example app demonstrates some of the basic syntax to get Bugsnag error reporting configured in your Python code.
# ***********************************************************

import bugsnag

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
    ignore_classes = ['DontCare'],

    # Defines the release stage for all events that occur in this app.
    release_stage = 'development',

    # Defines which release stages bugsnag should report. e.g. ignore staging errors.
    notify_release_stages = [ 'development', 'production'],

    # Any param key that contains one of these strings will be filtered out of all error reports.
    params_filters = ['credit_card_number', 'password', 'ssn'],

    # We mark stacktrace lines as inProject if they come from files inside root:
    # project_root = "/path/to/your/app",

    # Useful if you are wrapping bugsnag.notify() in with your own library, to ensure errors group properly.
    # traceback_exclude_module = [myapp.custom_logging],

)


def callback(notification):
    """This callback will evaluate and modify every exception report, handled and unhandled, that occurs within the app, right before it is sent to Bugsnag.
    """
    # adding user info and metadata to every report:
    notification.user = {
        'name': 'Alan Turing',
        'email': 'turing@code.net',
        'id': '1234567890',
    }

    notification.add_tab(
        'company', {
            'name': 'Stark Industries'
        }
    )
    # checks every error, and adds special metadata only when the error class is 'SpecificError', as in crash_with_callback(), below.
    if isinstance(notification.exception, SpecificError):
        tab = {
            'message': 'That\'s not how this works',
            'code': 500,
            'password': 'ue$hs_9gFsd!kjl41___' # this will be redacted by your filter.
        }
        notification.add_tab('Diagnostics', tab)
        notification.context = 'Check the \'Diagnostics\' tab attached only to SpecificErrors'

# attach the callback function to your Bugsnag client.
bugsnag.before_notify(callback)


# defining our own error class, as an example.
class SpecificError(Exception):
    pass


def crash_dict():
    """Deliberately triggers an unhandled KeyError to be reported by the bugsnag exception handler, and crash the app.
    """
    things = { 'object': 'value'}
    return things['not_a_key']


def crash_callback():
    """Deliberately raises an unhandled error which will have diagnostic data attached by the before_notify() callback above, and crash the app.
    """
    raise(SpecificError('SomethingBad'))


def handle_zero_div():
    """Deliberately triggers a handled exception, and reports it to Bugsnag.
    """
    try:
        x = 1/0
    except Exception as e:
        bugsnag.notify(e)

    print('The app hasn\'t crashed, but check https://app.bugsnag.com to view notifications')


if __name__ == '__main__':
    # automatically sends this manual notification every time the file is loaded.
    bugsnag.notify(Exception('File loaded!'))

    print("""
    This app sends one notification to your Bugsnag dashboard on loading.

    call this function to send more handled exceptions:
    -  handle_zero_div()

    call these functions to crash the app and send unhandled exceptions:
    -  crash_dict()
    -  crash_callback()

    or, just write your own crashing statements to see how Bugsnag reports them!
    """)
