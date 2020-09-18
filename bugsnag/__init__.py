import sys
import logging
from types import TracebackType
from typing import Optional, Union, Tuple, Type

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification
from bugsnag.event import Event
from bugsnag.client import Client
from bugsnag.legacy import (configure, configure_request, add_metadata_tab,
                            clear_request_config, before_notify, send_sessions)

__all__ = ('Client', 'Event', 'Configuration', 'RequestConfiguration',
           'configuration', 'configure', 'configure_request',
           'add_metadata_tab', 'clear_request_config', 'notify',
           'auto_notify', 'before_notify', 'start_session',
           'send_sessions', 'auto_notify_exc_info',
           'Notification')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    '%(asctime)s - [%(name)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

default_client = None  # type: Optional[Client]
ExcInfoType = Tuple[Type, BaseException, TracebackType]


def notify(exception: Union[BaseException, ExcInfoType], **options):
    """
    Notify bugsnag of an exception. Must be called after bugsnag.start().
    """
    if 'severity' in options:
        options['severity_reason'] = {'type': 'userSpecifiedSeverity'}
    else:
        options['severity_reason'] = {'type': 'handledException'}

    if (isinstance(exception, (list, tuple)) and len(exception) == 3 and
            isinstance(exception[2], TracebackType)):
        default_client.notify_exc_info(*exception, **options)
    else:
        if not isinstance(exception, BaseException):
            try:
                value = repr(exception)
            except Exception:
                value = '[BADENCODING]'

            logger.warning('Coercing invalid notify()'
                           ' value to RuntimeError: %s' % value)
            exception = RuntimeError(value)

        default_client.notify(exception, **options)


def start_session():
    """
    Delivers all currently undelivered sessions to Bugsnag
    Must be called after bugsnag.start().
    """
    default_client.session_tracker.start_session()


def auto_notify(exception: BaseException, **options):
    """
    Notify bugsnag of an exception if auto_notify is enabled.
    Must be called after bugsnag.start().
    """
    if default_client.configuration.auto_notify:
        default_client.notify(
            exception,
            unhandled=options.pop('unhandled', True),
            severity=options.pop('severity', 'error'),
            severity_reason=options.pop('severity_reason', {
                'type': 'unhandledException'
            }),
            **options
        )


def auto_notify_exc_info(exc_info: Optional[ExcInfoType] = None, **options):
    """
    Notify bugsnag of a exc_info tuple if auto_notify is enabled
    Must be called after bugsnag.start().
    """
    if default_client.configuration.auto_notify:
        info = exc_info or sys.exc_info()
        if info is not None:
            exc_type, value, tb = info
            default_client.notify_exc_info(
                exc_type, value, tb,
                unhandled=options.pop('unhandled', True),
                severity=options.pop('severity', 'error'),
                severity_reason=options.pop('severity_reason', {
                    'type': 'unhandledException'
                }),
                **options
            )
