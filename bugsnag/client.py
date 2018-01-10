import sys

from functools import wraps
from types import FunctionType

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification
from bugsnag.handlers import BugsnagHandler
from bugsnag.sessiontracker import SessionTracker

import bugsnag


__all__ = ('Client',)


class Client(object):
    """
    A Bugsnag monitoring and reporting client.

    >>> client = Client(api_key='...')
    """

    def __init__(self, configuration=None, install_sys_hook=True, **kwargs):
        self.configuration = configuration or Configuration()
        self.session_tracker = SessionTracker(self.configuration)
        self.configuration.configure(**kwargs)

        if install_sys_hook:
            self.install_sys_hook()

    def capture(self, exceptions=None, **options):
        """
        Run a block of code within the clients context.
        Any exception raised will be reported to bugsnag.

        >>> with client.capture():
        >>>     raise Exception('an exception passed to bugsnag then reraised')

        The context can optionally include specific types to capture.

        >>> with client.capture((TypeError,)):
        >>>     raise Exception('an exception which does get captured')

        Alternately, functions can be decorated to capture any
        exceptions thrown during execution and reraised.

        >>> @client.capture
        >>> def foo():
        >>>     raise Exception('an exception passed to bugsnag then reraised')

        The decoration can optionally include specific types to capture.

        >>> @client.capture((TypeError,))
        >>> def foo():
        >>>     raise Exception('an exception which does not get captured')
        """

        if isinstance(exceptions, FunctionType):
            return ClientContext(self, (Exception,))(exceptions)

        return ClientContext(self, exceptions, **options)

    def notify(self, exception, **options):
        """
        Notify bugsnag of an exception.

        >>> client.notify(Exception('Example'))
        """

        notification = Notification(exception, self.configuration,
                                    RequestConfiguration.get_instance(),
                                    **options)
        self.deliver(notification)

    def notify_exc_info(self, exc_type, exc_value, traceback, **options):
        """
        Notify bugsnag of an exception via exc_info.

        >>> client.notify_exc_info(*sys.exc_info())
        """

        exception = exc_value
        options['traceback'] = traceback
        notification = Notification(exception, self.configuration,
                                    RequestConfiguration.get_instance(),
                                    **options)
        self.deliver(notification)

    def excepthook(self, exc_type, exc_value, traceback):
        if self.configuration.auto_notify:
            self.notify_exc_info(
                exc_type, exc_value, traceback,
                severity='error',
                unhandled=True,
                severity_reason={
                    'type': 'unhandledException'
                })

    def install_sys_hook(self):
        self.sys_excepthook = sys.excepthook

        def excepthook(*exc_info):
            self.excepthook(*exc_info)

            if self.sys_excepthook:
                self.sys_excepthook(*exc_info)

        sys.excepthook = excepthook
        sys.excepthook.bugsnag_client = self

    def uninstall_sys_hook(self):
        client = getattr(sys.excepthook, 'bugsnag_client', None)

        if client is self:
            sys.excepthook = self.sys_excepthook
            self.sys_excepthook = None

    def deliver(self, notification):  # type: (Notification) -> None
        """
        Deliver the exception notification to Bugsnag.
        """

        if not self.should_deliver(notification):
            return

        initial_severity = notification.severity
        initial_reason = notification.severity_reason

        def send_payload():
            if notification.api_key is None:
                bugsnag.logger.warning(
                    "No API key configured, couldn't notify")
                return

            if initial_severity != notification.severity:
                notification.severity_reason = {
                    'type': 'userCallbackSetSeverity'
                }
            else:
                notification.severity_reason = initial_reason
            payload = notification._payload()
            try:
                self.configuration.delivery.deliver(self.configuration,
                                                    payload)
            except Exception as e:
                bugsnag.logger.exception('Notifying Bugsnag failed %s', e)
            # Trigger session delivery
            self.session_tracker.send_sessions()

        self.configuration.middleware.run(notification, send_payload)

    def should_deliver(self, notification):  # type: (Notification) -> bool
        # Return early if we shouldn't notify for current release stage
        if not self.configuration.should_notify():
            return False

        # Return early if we should ignore exceptions of this type
        if self.configuration.should_ignore(notification.exception):
            return False

        return True

    def log_handler(self, extra_fields=None):
        return BugsnagHandler(client=self, extra_fields=extra_fields)


class ClientContext(object):
    def __init__(self, client, exception_types=None, **options):
        self.client = client
        self.options = options
        if 'severity' in options:
            options['severity_reason'] = dict(type='userContextSetSeverity')
        self.exception_types = exception_types or (Exception,)

    def __call__(self, function):
        @wraps(function)
        def decorate(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except self.exception_types as e:
                self.client.notify(e, source_func=function, **self.options)
                raise

        return decorate

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        if any(exc_info):
            if any(isinstance(exc_info[1], e) for e in self.exception_types):
                self.client.notify_exc_info(*exc_info, **self.options)

        return False
