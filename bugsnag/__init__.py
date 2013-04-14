import sys

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification


configuration = Configuration()


def configure(**options):
    """
    Configure the Bugsnag notifier application-wide settings.
    """
    configuration.configure(**options)


def configure_request(**options):
    """
    Configure the Bugsnag notifier per-request settings.
    """
    RequestConfiguration.get_instance().configure(**options)


def clear_request_config():
    """
    Clears the per-request settings.
    """
    RequestConfiguration.clear()


def notify(exception, **options):
    """
    Notify bugsnag of an exception.
    """
    if isinstance(exception, (list, tuple)):
        # Exception tuples, eg. from sys.exc_info
        if not "traceback" in options:
            options["traceback"] = exception[2]

        Notification(exception[1], configuration,
                     RequestConfiguration.get_instance(), **options).deliver()
    else:
        # Exception objects
        Notification(exception, configuration,
                     RequestConfiguration.get_instance(), **options).deliver()


def auto_notify(exception, **options):
    """
    Notify bugsnag of an exception if auto_notify is enabled.
    """
    if configuration.auto_notify:
        notify(exception, **options)


def log(message):
    """
    Print a log message with a Bugsnag prefix.
    """
    print("** [Bugsnag] %s" % message)


def warn(message):
    """
    Print a warning message with a Bugsnag prefix.
    """
    sys.stderr.write("** [Bugsnag] WARNING: %s\n" % message)


# Hook into all uncaught exceptions
def __bugsnag_excepthook(exctype, exception, traceback):
    auto_notify(exception, traceback=traceback)
    _old_excepthook(exctype, exception, traceback)

_old_excepthook = sys.excepthook
sys.excepthook = __bugsnag_excepthook
