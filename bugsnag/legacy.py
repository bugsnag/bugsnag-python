from typing import Dict, Any, Tuple, Type, Optional, Union, List
import types
import sys

from bugsnag.breadcrumbs import BreadcrumbType, OnBreadcrumbCallback
from bugsnag.feature_flags import FeatureFlag
from bugsnag.configuration import RequestConfiguration
from bugsnag.client import Client

default_client = Client()
configuration = default_client.configuration
logger = configuration.logger
ExcInfoType = Tuple[Type, Exception, types.TracebackType]


__all__ = ('configure', 'configure_request', 'add_metadata_tab',
           'clear_request_config', 'notify', 'start_session', 'auto_notify',
           'auto_notify_exc_info', 'before_notify', 'leave_breadcrumb')


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


def add_metadata_tab(tab_name: str, data: Dict[str, Any]):
    """
    Add metaData to the tab

    bugsnag.add_metadata_tab("user", {"id": "1", "name": "Conrad"})
    """
    metadata = RequestConfiguration.get_instance().metadata
    if tab_name not in metadata:
        metadata[tab_name] = {}

    metadata[tab_name].update(data)


def clear_request_config():
    """
    Clears the per-request settings.
    """
    RequestConfiguration.clear()


def notify(exception: BaseException, **options):
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

            default_client.configuration.logger.warning(
                'Coercing invalid notify() value to RuntimeError: %s' % value
            )

            exception = RuntimeError(value)

        default_client.notify(exception, **options)


def start_session():
    """
    Creates a new session
    """
    default_client.session_tracker.start_session()


def auto_notify(exception: BaseException, **options):
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


def auto_notify_exc_info(exc_info: Optional[ExcInfoType] = None, **options):
    """
    Notify bugsnag of a exc_info tuple if auto_notify is enabled
    """
    if configuration.auto_notify:
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


def before_notify(callback):
    """
    Add a callback to be called before bugsnag is notified

    This can be used to alter the event before sending it to Bugsnag.
    """
    configuration.middleware.before_notify(callback)


def leave_breadcrumb(
    message: str,
    metadata: Dict[str, Any] = {},
    type: BreadcrumbType = BreadcrumbType.MANUAL
) -> None:
    default_client.leave_breadcrumb(message, metadata, type)


def add_on_breadcrumb(on_breadcrumb: OnBreadcrumbCallback) -> None:
    """
    Add a callback to be called each time a breadcrumb is left

    This can be used to alter the breadcrumb, or discard it by returning False
    """
    default_client.add_on_breadcrumb(on_breadcrumb)


def remove_on_breadcrumb(on_breadcrumb: OnBreadcrumbCallback) -> None:
    """
    Remove an existing on_breadcrumb callback
    """
    default_client.remove_on_breadcrumb(on_breadcrumb)


def _auto_leave_breadcrumb(
    message: str,
    metadata: Dict[str, Any],
    type: BreadcrumbType
) -> None:
    default_client._auto_leave_breadcrumb(message, metadata, type)


def add_feature_flag(
    name: Union[str, bytes],
    variant: Union[None, str, bytes] = None
) -> None:
    default_client.add_feature_flag(name, variant)


def add_feature_flags(feature_flags: List[FeatureFlag]) -> None:
    default_client.add_feature_flags(feature_flags)


def clear_feature_flag(name: Union[str, bytes]) -> None:
    default_client.clear_feature_flag(name)


def clear_feature_flags() -> None:
    default_client.clear_feature_flags()
