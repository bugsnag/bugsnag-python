import types
import sys
import logging

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification
from bugsnag.client import Client


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    '%(asctime)s - [%(name)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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


def add_metadata_tab(tab_name, data):
    """
    Add metaData to the tab

    bugsnag.add_metadata_tab("user", {"id": "1", "name": "Conrad"})
    """
    meta_data = RequestConfiguration.get_instance().meta_data
    if tab_name not in meta_data:
        meta_data[tab_name] = {}

    meta_data[tab_name].update(data)


def clear_request_config():
    """
    Clears the per-request settings.
    """
    RequestConfiguration.clear()


def notify(exception, **options):
    """
    Notify bugsnag of an exception.
    """
    if isinstance(exception, (list, tuple)) and len(exception) > 1:
        # Exception tuples, eg. from sys.exc_info
        if 'traceback' not in options and len(exception) > 2:
            if isinstance(exception[2], types.TracebackType):
                options["traceback"] = exception[2]

        exception = exception[1]

    if not isinstance(exception, BaseException):
        try:
            value = repr(exception)
        except:
            value = '[BADENCODING]'

        logger.warning('Coercing invalid bugnsag.notify()'
                       ' value to RuntimeError: %s' % value)
        exception = RuntimeError(value)

    Notification(exception, configuration,
                 RequestConfiguration.get_instance(),
                 **options).deliver()


def auto_notify(exception, **options):
    """
    Notify bugsnag of an exception if auto_notify is enabled.
    """
    if configuration.auto_notify:
        notify(exception, severity="error", **options)


def before_notify(callback):
    """
    Add a callback to be called before bugsnag is notified

    This can be used to alter the notification before sending it to Bugsnag.
    """
    configuration.middleware.before_notify(callback)


# Hook into all uncaught exceptions
def __bugsnag_excepthook(exctype, exception, traceback):
    try:
        auto_notify(exception, traceback=traceback)
    except:
        logger.exception('Error in excepthook, probably shutting down.')

    _old_excepthook(exctype, exception, traceback)

_old_excepthook = sys.excepthook
sys.excepthook = __bugsnag_excepthook
