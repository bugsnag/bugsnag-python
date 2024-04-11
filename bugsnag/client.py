import builtins
import sys
import threading
import warnings
import functools

from datetime import datetime, timezone
from typing import Union, Tuple, Callable, Optional, List, Type, Dict, Any

from bugsnag.breadcrumbs import (
    Breadcrumb,
    BreadcrumbType,
    OnBreadcrumbCallback
)
from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.event import Event
from bugsnag.feature_flags import FeatureFlag
from bugsnag.handlers import BugsnagHandler
from bugsnag.sessiontracker import SessionTracker
from bugsnag.utils import to_rfc3339
from bugsnag.context import ContextLocalState
from bugsnag.request_tracker import RequestTracker

__all__ = ('Client',)


class Client:
    """
    A Bugsnag monitoring and reporting client.

    >>> client = Client(api_key='...')  # doctest: +SKIP
    """

    def __init__(self, configuration: Optional[Configuration] = None,
                 install_sys_hook=True, **kwargs):
        self.configuration = configuration or Configuration()  # type: Configuration  # noqa: E501
        self.session_tracker = SessionTracker(self.configuration)
        self.configuration.configure(**kwargs)
        self._context = ContextLocalState(self)
        self._request_tracker = RequestTracker()

        if install_sys_hook:
            self.install_sys_hook()

    def capture(self,
                exceptions: Union[Tuple[Type, ...], Callable, None] = None,
                **options):
        """
        Run a block of code within the clients context.
        Any exception raised will be reported to bugsnag.

        >>> with client.capture():  # doctest: +SKIP
        ...     raise Exception('an exception passed to bugsnag then reraised')

        The context can optionally include specific types to capture.

        >>> with client.capture((TypeError,)):  # doctest: +SKIP
        ...     raise Exception('an exception which does get captured')

        Alternately, functions can be decorated to capture any
        exceptions thrown during execution and reraised.

        >>> @client.capture  # doctest: +SKIP
        ... def foo():
        ...     raise Exception('an exception passed to bugsnag then reraised')

        The decoration can optionally include specific types to capture.

        >>> @client.capture((TypeError,))  # doctest: +SKIP
        ... def foo():
        ...     raise Exception('an exception which does not get captured')
        """

        if callable(exceptions):
            return ClientContext(self, (Exception,))(exceptions)

        return ClientContext(self, exceptions, **options)

    def notify(self, exception: BaseException, asynchronous=None, **options):
        """
        Notify bugsnag of an exception.

        >>> client.notify(Exception('Example'))  # doctest: +SKIP
        """

        event = Event(
            exception,
            self.configuration,
            RequestConfiguration.get_instance(),
            **options,
            feature_flag_delegate=self._context.feature_flag_delegate
        )

        self._leave_breadcrumb_for_event(event)
        self.deliver(event, asynchronous=asynchronous)

    def notify_exc_info(self, exc_type, exc_value, traceback,
                        asynchronous=None, **options):
        """
        Notify bugsnag of an exception via exc_info.

        >>> client.notify_exc_info(*sys.exc_info())  # doctest: +SKIP
        """

        exception = exc_value
        options['traceback'] = traceback
        event = Event(
            exception,
            self.configuration,
            RequestConfiguration.get_instance(),
            **options,
            feature_flag_delegate=self._context.feature_flag_delegate
        )

        self._leave_breadcrumb_for_event(event)
        self.deliver(event, asynchronous=asynchronous)

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

        if hasattr(threading, 'excepthook'):
            self.threading_excepthook = threading.excepthook

            def threadhook(args):
                self.excepthook(args[0], args[1], args[2])

                if self.threading_excepthook:
                    self.threading_excepthook(args)

            threading.excepthook = threadhook
            threading.excepthook.bugsnag_client = self

    def uninstall_sys_hook(self):
        client = getattr(sys.excepthook, 'bugsnag_client', None)

        if client is self:
            sys.excepthook = self.sys_excepthook
            self.sys_excepthook = None

        if hasattr(threading, 'excepthook'):
            client = getattr(threading.excepthook, 'bugsnag_client', None)
            if client is self:
                threading.excepthook = self.threading_excepthook
                self.threading_excepthook = None

    def deliver(self, event: Event,
                asynchronous: Optional[bool] = None):
        """
        Deliver the exception event to Bugsnag.
        """

        if not self.should_deliver(event):
            return

        def run_middleware():
            initial_severity = event.severity
            initial_reason = event.severity_reason.copy()

            def send_payload():
                if event.api_key is None:
                    self.configuration.logger.warning(
                        "No API key configured, couldn't notify"
                    )

                    return

                if initial_severity != event.severity:
                    event.severity_reason = {
                        'type': 'userCallbackSetSeverity'
                    }
                else:
                    event.severity_reason = initial_reason

                payload = event._payload()

                post_delivery_callback = self._request_tracker.new_request()
                options = {'post_delivery_callback': post_delivery_callback}

                if asynchronous is not None:
                    options['asynchronous'] = asynchronous

                try:
                    self.configuration.delivery.deliver(
                        self.configuration,
                        payload,
                        options
                    )
                except Exception as e:
                    self.configuration.logger.exception(
                        'Notifying Bugsnag failed %s',
                        e
                    )

                    # ensure this request is not still marked as in-flight
                    post_delivery_callback()

                # Trigger session delivery
                self.session_tracker.send_sessions()

            self.configuration.middleware.run(event, send_payload)

        self.configuration.internal_middleware.run(event, run_middleware)

    def should_deliver(self, event: Event) -> bool:
        # Return early if we shouldn't notify for current release stage
        if not self.configuration.should_notify():
            return False

        # Return early if we should ignore these errors
        if self.configuration.should_ignore(event.errors):
            return False

        return True

    def log_handler(
        self,
        extra_fields: Optional[List[str]] = None
    ) -> BugsnagHandler:
        return BugsnagHandler(client=self, extra_fields=extra_fields)

    @property
    def feature_flags(self) -> List[FeatureFlag]:
        return self._context.feature_flag_delegate.to_list()

    def add_feature_flag(
        self,
        name: Union[str, bytes],
        variant: Union[None, str, bytes] = None
    ) -> None:
        self._context.feature_flag_delegate.add(name, variant)

    def add_feature_flags(self, feature_flags: List[FeatureFlag]) -> None:
        self._context.feature_flag_delegate.merge(feature_flags)

    def clear_feature_flag(self, name: Union[str, bytes]) -> None:
        self._context.feature_flag_delegate.remove(name)

    def clear_feature_flags(self) -> None:
        self._context.feature_flag_delegate.clear()

    @property
    def breadcrumbs(self) -> List[Breadcrumb]:
        return self.configuration.breadcrumbs

    def add_on_breadcrumb(self, on_breadcrumb: OnBreadcrumbCallback) -> None:
        self.configuration.add_on_breadcrumb(on_breadcrumb)

    def remove_on_breadcrumb(
        self,
        on_breadcrumb: OnBreadcrumbCallback
    ) -> None:
        self.configuration.remove_on_breadcrumb(on_breadcrumb)

    def leave_breadcrumb(
        self,
        message: str,
        metadata: Dict[str, Any] = {},
        type: BreadcrumbType = BreadcrumbType.MANUAL
    ) -> None:
        # Don't create breadcrumbs if the max_breadcrumbs is 0 as they would
        # be immediately discarded anyway
        if self.configuration.max_breadcrumbs == 0:
            return

        if not isinstance(type, BreadcrumbType):
            type = BreadcrumbType.MANUAL

        if not isinstance(metadata, dict):
            warning_message = 'breadcrumb metadata must be a dict, got {}'
            warnings.warn(
                warning_message.format(builtins.type(metadata).__name__),
                RuntimeWarning
            )

            metadata = {}

        timestamp = to_rfc3339(datetime.now(timezone.utc))
        breadcrumb = Breadcrumb(message, type, metadata, timestamp)

        for callback in self.configuration._on_breadcrumbs:
            try:
                should_continue = callback(breadcrumb)

                if should_continue is False:
                    self.configuration.logger.info(
                        'Breadcrumb not attached due to on_breadcrumb callback'
                    )

                    return
            except Exception:
                self.configuration.logger.exception(
                    'Exception raised in on_breadcrumb callback'
                )

        self.configuration._breadcrumbs.append(breadcrumb)

    def _auto_leave_breadcrumb(
        self,
        message: str,
        metadata: Dict[str, Any],
        type: BreadcrumbType
    ) -> None:
        if type in self.configuration.enabled_breadcrumb_types:
            self.leave_breadcrumb(message, metadata, type)

    def _leave_breadcrumb_for_event(self, event: Event) -> None:
        error_class = event.errors[0].error_class

        self._auto_leave_breadcrumb(
            error_class,
            {
                'errorClass': error_class,
                'message': event.errors[0].error_message,
                'unhandled': event.unhandled,
                'severity': event.severity,
            },
            BreadcrumbType.ERROR
        )

    def flush(self, timeout_ms: int) -> None:
        # trigger session delivery as there may be outstanding sessions that
        # haven't been sent yet
        self.session_tracker.send_sessions()

        stop_event = threading.Event()

        def block_until_no_requests():
            while (
                self._request_tracker.has_in_flight_requests() or
                self.session_tracker._request_tracker.has_in_flight_requests()
            ):
                # wait 10ms before checking for in-flight requests again
                was_stopped = stop_event.wait(0.01)

                # stop checking and exit if the timeout has been exceeded
                if was_stopped:
                    break

        thread = threading.Thread(target=block_until_no_requests)
        thread.start()
        thread.join(timeout_ms / 1000)

        if thread.is_alive():
            # tell the thread to stop checking for in-flight requests as the
            # timeout has been exceeded
            stop_event.set()

            raise Exception("flush timed out after %dms" % timeout_ms)

    def add_metadata_tab(self, tab_name: str, data: Dict[str, Any]) -> None:
        metadata = RequestConfiguration.get_instance().metadata

        if tab_name not in metadata:
            metadata[tab_name] = {}

        metadata[tab_name].update(data)

    def aws_lambda_handler(
        self,
        real_handler: Optional[Callable] = None,
        flush_timeout_ms: int = 2000,
        lambda_timeout_notify_ms: int = 1000,
    ) -> Callable:
        # handle being called with just 'flush_timeout_ms'
        if real_handler is None:
            return functools.partial(
                self.aws_lambda_handler,
                flush_timeout_ms=flush_timeout_ms,
                lambda_timeout_notify_ms=lambda_timeout_notify_ms,
            )

        # attributes from the aws context that we want to capture as metadata
        # the context is an instance of LambdaContext, which isn't iterable and
        # so can't be added to metadata as-is
        aws_context_attributes = [
            'function_name',
            'function_version',
            'invoked_function_arn',
            'memory_limit_in_mb',
            'aws_request_id',
            'log_group_name',
            'log_stream_name',
            'identity',
            'client_context',
        ]

        @functools.wraps(real_handler)
        def wrapped_handler(aws_event, aws_context):
            timer = None
            aws_context_metadata = {
                attribute:
                    getattr(aws_context, attribute, None)
                    for attribute in aws_context_attributes
            }

            if lambda_timeout_notify_ms > 0:
                # reporting possible timeouts is done using a separate thread,
                # but we don't want to lose the information from the main
                # thread so we store references here to use later
                # TODO: we shouldn't have 3 places where per-request data is
                #       stored - it should all be in 'self._context'
                main_request_config = RequestConfiguration.get_instance()
                main_request_breadcrumbs = \
                    self.configuration._breadcrumbs._breadcrumbs
                main_request_feature_flags = \
                    self._context.feature_flag_delegate._storage

                def report_timeout_to_bugsnag():
                    # copy over the main thread's data to this thread
                    RequestConfiguration.set_instance(main_request_config)

                    self.configuration._breadcrumbs._breadcrumbs.extend(
                        main_request_breadcrumbs
                    )

                    self._context.feature_flag_delegate.merge(
                        main_request_feature_flags.values()
                    )

                    # generate an empty traceback object so the lambda timeout
                    # doesn't have a misleading traceback
                    try:
                        raise Exception()
                    except Exception as exception:
                        empty_traceback = exception.__traceback__

                    lambda_timeout_approaching = LambdaTimeoutApproaching(
                        aws_context.get_remaining_time_in_millis(),
                        empty_traceback
                    )

                    # set the source_func so the user's lambda handler is the
                    # only item in the traceback
                    self.notify(
                        lambda_timeout_approaching,
                        source_func=real_handler
                    )

                remaining_ms = aws_context.get_remaining_time_in_millis()
                timer = threading.Timer(
                    (remaining_ms - lambda_timeout_notify_ms) / 1000,
                    report_timeout_to_bugsnag
                )

                timer.start()

            try:
                self.add_metadata_tab('AWS Lambda Event', aws_event)
                self.add_metadata_tab(
                    'AWS Lambda Context',
                    aws_context_metadata
                )

                if self.configuration.auto_capture_sessions:
                    self.session_tracker.start_session()

                return real_handler(aws_event, aws_context)
            except Exception as exception:
                if self.configuration.auto_notify:
                    self.notify(
                        exception,
                        unhandled=True,
                        severity='error',
                        severity_reason={'type': 'unhandledException'},
                    )

                raise
            finally:
                # a timer can only be cancelled if it hasn't fired yet
                if timer and timer.is_alive():
                    timer.cancel()

                try:
                    self.flush(flush_timeout_ms)
                except Exception as exception:
                    warnings.warn(
                        'Delivery may be unsuccessful: ' + str(exception)
                    )

        return wrapped_handler


class ClientContext:
    def __init__(self, client,
                 exception_types: Optional[Tuple[Type, ...]] = None,
                 **options):
        self.client = client
        self.options = options
        if 'severity' in options:
            options['severity_reason'] = dict(type='userContextSetSeverity')
        self.exception_types = exception_types or (Exception,)

    def __call__(self, function: Callable):
        @functools.wraps(function)
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


class LambdaTimeoutApproaching(Exception):
    def __init__(self, remaining_ms: int, tb):
        super().__init__('Lambda will timeout in %dms' % remaining_ms)
        self.__traceback__ = tb
