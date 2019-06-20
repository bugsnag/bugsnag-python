from bugsnag_logger import logger
# This file demonstrates how errors will be reported to bugsnag through your logger, even without any explicit reference to bugsnag in your python code.

print("""
This app logs 3 errors to your Bugsnag dashboard on loading.

call these functions to send more handled exceptions:
-  handle_zero_div()
-  log_error()

call these functions to crash the app and send unhandled exceptions:
-  crash_dict()
-  crash_callback()

or, just write your own crashing statements to see how Bugsnag reports them!
""")

class SpecificError(Exception):
    pass

def crash_dict():
    """Deliberately triggers an unhandled KeyError to be reported by the bugsnag exception handler, and crash the app.
    """
    things = { 'object': 'value'}
    return things['not_a_key']


def crash_callback():
    """Deliberately raises an unhandled error which will have diagnostic data attached by the global callback function in bugsnag_logger, and crash the app.
    """
    raise(SpecificError('SomethingBad'))


def handle_zero_div():
    """Deliberately triggers a handled exception, and reports it to Bugsnag.
    """
    try:
        x = 1/0
    except Exception as e:
        logger.warn(e)

    print('The app hasn\'t crashed, but check https://app.bugsnag.com to view notifications')

def log_error():
    """Simply logs an error, which will also be sent to your Bugsnag dashboard.
    """
    logger.error('I forgot my lunch at home')
    print('Check bugsnag.com to view this log report.')


if __name__ == '__main__':
    # First one will not report to Bugsnag because it is below handler.setLevel()
    logger.info('This is purely informational.')
    logger.warn('This is a warning!')
    logger.error('This didn\'t go well.')
    logger.critical(Exception('The system is down!'))
