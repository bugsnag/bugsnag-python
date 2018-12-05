import types

from bugsnag.configuration import RequestConfiguration
from bugsnag.client import Client

import bugsnag

default_client = Client()
configuration = default_client.configuration


def configure(**options):
    """
    Configure the Bugsnag notifier application-wide settings.
    """
    return configuration.configure(**options)


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
    if 'severity' in options:
        options['severity_reason'] = {'type': 'userSpecifiedSeverity'}
    else:
        options['severity_reason'] = {'type': 'handledException'}

    if (isinstance(exception, (list, tuple)) and len(exception) == 3 and
            isinstance(exception[2], types.TracebackType)):
        default_client.notify_exc_info(*exception, **options)
    else:
        if not isinstance(exception, BaseException):
            try:
                value = repr(exception)
            except Exception:
                value = '[BADENCODING]'

            bugsnag.logger.warning('Coercing invalid notify()'
                                   ' value to RuntimeError: %s' % value)
            exception = RuntimeError(value)

        default_client.notify(exception, **options)


def start_session():
    """
    Creates a new session
    """
    default_client.session_tracker.start_session()


def send_sessions():
    """
    Delivers all currently undelivered sessions to Bugsnag
    """
    default_client.session_tracker.send_sessions()


def auto_notify(exception, **options):
    """
    Notify bugsnag of an exception if auto_notify is enabled.
    """
    if configuration.auto_notify:
        default_client.notify(
            exception,
            unhandled=options.pop('unhandled', True),
            severity=options.pop('severity', 'error'),
            severity_reason=options.pop('severity_reason', {
                'type': 'unhandledException'
            }),
            **options
        )


def before_notify(callback):
    """
    Add a callback to be called before bugsnag is notified

    This can be used to alter the notification before sending it to Bugsnag.
    """
    configuration.middleware.before_notify(callback)
