import os
import platform
import socket
import sys
import sysconfig
from typing import List, Any, Tuple, Union, Optional
import warnings
import logging
from threading import Lock

from bugsnag.breadcrumbs import (
    BreadcrumbType,
    Breadcrumb,
    Breadcrumbs,
    OnBreadcrumbCallback
)
from bugsnag.sessiontracker import SessionMiddleware
from bugsnag.middleware import DefaultMiddleware, MiddlewareStack
from bugsnag.utils import (fully_qualified_class_name, validate_str_setter,
                           validate_bool_setter, validate_iterable_setter,
                           validate_required_str_setter, validate_int_setter)
from bugsnag.delivery import (create_default_delivery, DEFAULT_ENDPOINT,
                              DEFAULT_SESSIONS_ENDPOINT)
from bugsnag.uwsgi import warn_if_running_uwsgi_without_threads

try:
    from contextvars import ContextVar
    _request_info = ContextVar('bugsnag-request', default=None)  # type: ignore
except ImportError:
    from bugsnag.utils import ThreadContextVar
    _request_info = ThreadContextVar('bugsnag-request', default=None)  # type: ignore  # noqa: E501


__all__ = ('Configuration', 'RequestConfiguration')
_sentinel = object()


class Configuration:
    """
    Global app-level Bugsnag configuration settings.
    """

    def __init__(self, logger=_sentinel):
        self._mutex = Lock()

        self.api_key = os.environ.get('BUGSNAG_API_KEY', None)
        self.release_stage = os.environ.get("BUGSNAG_RELEASE_STAGE",
                                            "production")
        self.notify_release_stages = None
        self.auto_notify = True
        self.send_code = True
        self.send_environment = False
        self.asynchronous = True
        self.delivery = create_default_delivery()
        self.lib_root = sysconfig.get_path('purelib')
        self.project_root = os.getcwd()
        self.app_type = None
        self.app_version = None
        self.params_filters = ["password", "password_confirmation", "cookie",
                               "authorization"]
        self.ignore_classes = [
            "KeyboardInterrupt",
            "django.http.Http404",
            "django.http.response.Http404",
        ]
        self.endpoint = DEFAULT_ENDPOINT
        self.session_endpoint = DEFAULT_SESSIONS_ENDPOINT
        self.auto_capture_sessions = True
        self.traceback_exclude_modules = []

        self.middleware = MiddlewareStack()

        self.internal_middleware = MiddlewareStack()
        self.internal_middleware.append(DefaultMiddleware)
        self.internal_middleware.append(SessionMiddleware)

        self.proxy_host = None

        if not os.getenv("DYNO"):
            self.hostname = socket.gethostname()
        else:
            self.hostname = None

        self.runtime_versions = {"python": platform.python_version()}

        self.logger = logger

        self._max_breadcrumbs = 25
        self.breadcrumb_log_level = logging.INFO
        self.enabled_breadcrumb_types = list(BreadcrumbType)
        self._breadcrumbs = Breadcrumbs(self.max_breadcrumbs)
        self._on_breadcrumbs = []

    def configure(self, api_key=None, app_type=None, app_version=None,
                  asynchronous=None, auto_notify=None,
                  auto_capture_sessions=None, delivery=None, endpoint=None,
                  hostname=None, ignore_classes=None, lib_root=None,
                  notify_release_stages=None, params_filters=None,
                  project_root=None, proxy_host=None, release_stage=None,
                  send_code=None, send_environment=None, session_endpoint=None,
                  traceback_exclude_modules=None, logger=_sentinel,
                  breadcrumb_log_level=None, enabled_breadcrumb_types=None,
                  max_breadcrumbs=None):
        """
        Validate and set configuration options. Will warn if an option is of an
        incorrect type.
        """
        if api_key is not None:
            self.api_key = api_key
        if app_type is not None:
            self.app_type = app_type
        if app_version is not None:
            self.app_version = app_version
        if asynchronous is not None:
            self.asynchronous = asynchronous
        if auto_notify is not None:
            self.auto_notify = auto_notify
        if auto_capture_sessions is not None:
            self.auto_capture_sessions = auto_capture_sessions
        if delivery is not None:
            self.delivery = delivery
        if endpoint is not None:
            self.endpoint = endpoint
        if hostname is not None:
            self.hostname = hostname
        if ignore_classes is not None:
            self.ignore_classes = ignore_classes
        if lib_root is not None:
            self.lib_root = lib_root
        if notify_release_stages is not None:
            self.notify_release_stages = notify_release_stages
        if params_filters is not None:
            self.params_filters = params_filters
        if project_root is not None:
            self.project_root = project_root
        if proxy_host is not None:
            self.proxy_host = proxy_host
        if release_stage is not None:
            self.release_stage = release_stage
        if send_code is not None:
            self.send_code = send_code
        if send_environment is not None:
            self.send_environment = send_environment
        if session_endpoint is not None:
            self.session_endpoint = session_endpoint
        if traceback_exclude_modules is not None:
            self.traceback_exclude_modules = traceback_exclude_modules
        if logger is not _sentinel:
            self.logger = logger
        if breadcrumb_log_level is not None:
            self.breadcrumb_log_level = breadcrumb_log_level
        if enabled_breadcrumb_types is not None:
            self.enabled_breadcrumb_types = enabled_breadcrumb_types
        if max_breadcrumbs is not None:
            self.max_breadcrumbs = max_breadcrumbs

        return self

    def get(self, name):
        """
        Get a single configuration option
        """
        warnings.warn('Using get() to retrieve a Configuration property is ' +
                      'deprecated in favor of referencing properties directly',
                      DeprecationWarning)
        return getattr(self, name)

    @property
    def api_key(self):
        """
        Unique application identifier
        """
        return self._api_key

    @api_key.setter  # type: ignore
    @validate_required_str_setter
    def api_key(self, value: str):
        self._api_key = value

    @property
    def app_type(self):
        """
        Category for the current application or task
        """
        return self._app_type

    @app_type.setter  # type: ignore
    @validate_str_setter
    def app_type(self, value: str):
        self._app_type = value

    @property
    def app_version(self):
        """
        Release version of the current application
        """
        return self._app_version

    @app_version.setter  # type: ignore
    @validate_str_setter
    def app_version(self, value: str):
        self._app_version = value

    @property
    def asynchronous(self):
        """
        If API requests should be sent asynchronously
        """
        return self._asynchronous

    @asynchronous.setter  # type: ignore
    @validate_bool_setter
    def asynchronous(self, value: bool):
        self._asynchronous = value
        if value:
            warn_if_running_uwsgi_without_threads()

    @property
    def auto_capture_sessions(self):
        """
        If sessions should be automatically detected and delivered from web
        request integrations
        """
        return self._auto_capture_sessions

    @auto_capture_sessions.setter  # type: ignore
    @validate_bool_setter
    def auto_capture_sessions(self, value: bool):
        self._auto_capture_sessions = value

    @property
    def auto_notify(self):
        """
        If uncaught exceptions should be automatically captured and reported
        """
        return self._auto_notify

    @auto_notify.setter  # type: ignore
    @validate_bool_setter
    def auto_notify(self, value: bool):
        self._auto_notify = value

    @property
    def delivery(self):
        """
        Transport mechanism used to make API requests. Implement the Delivery
        interface to customize how requests are sent.
        """
        return self._delivery

    @delivery.setter  # type: ignore
    def delivery(self, value):
        if hasattr(value, 'deliver') and callable(value.deliver):
            self._delivery = value
        else:
            message = ('delivery should implement Delivery interface, got ' +
                       '{0}. This will be an error in a future release.')
            warnings.warn(message.format(type(value).__name__), RuntimeWarning)

    @property
    def endpoint(self):
        """
        Event API endpoint. Set this property if using Bugsnag On-Premise.

        >>> config = Configuration()
        >>> config.endpoint = 'https://notify.bugsnag.example.co'
        """
        return self._endpoint

    @endpoint.setter  # type: ignore
    @validate_required_str_setter
    def endpoint(self, value: str):
        self._endpoint = value

    @property
    def hostname(self):
        """
        The host name of the application server. This value is automatically
        detected for Heroku applications and included in event device metadata.
        """
        return self._hostname

    @hostname.setter  # type: ignore
    @validate_str_setter
    def hostname(self, value: str):
        self._hostname = value

    @property
    def ignore_classes(self):
        """
        Fully qualified class names which should be ignored when capturing
        uncaught exceptions and other events. KeyboardInterrupt and Http404
        exceptions are ignored by default.
        """
        return self._ignore_classes

    @ignore_classes.setter  # type: ignore
    @validate_iterable_setter
    def ignore_classes(self, value: Union[List[str], Tuple[str]]):
        self._ignore_classes = value

    @property
    def lib_root(self):
        """
        The path to the Python library. Any traceback frame which contains
        lib_root as a prefix is considered out-of-project. The prefix is also
        stripped to make file names easier to read.
        """
        return self._lib_root

    @lib_root.setter  # type: ignore
    @validate_str_setter
    def lib_root(self, value: str):
        self._lib_root = value

    @property
    def notify_release_stages(self):
        """
        A list of release_stage values which are permitted to capture and send
        events and sessions. By default this value is None and all events and
        sessions are delivered.
        """
        return self._notify_release_stages

    @notify_release_stages.setter  # type: ignore
    @validate_iterable_setter
    def notify_release_stages(self, value: List[str]):
        self._notify_release_stages = value

    @property
    def params_filters(self):
        """
        A list of filters applied to event metadata to prevent the values from
        being sent in events. By default the following keys are filtered:

        * authorization
        * cookie
        * password
        * password_confirmation
        """
        return self._params_filters

    @params_filters.setter  # type: ignore
    @validate_iterable_setter
    def params_filters(self, value: List[str]):
        self._params_filters = value

    @property
    def project_root(self):
        """
        The working directory containing the application source code.
        Traceback file paths which contain this prefix are considered a part of
        the project. This prefix is also stripped to increase file name
        readability in traceback lines.
        """
        return self._project_root

    @project_root.setter  # type: ignore
    @validate_str_setter
    def project_root(self, value: str):
        self._project_root = value

    @property
    def proxy_host(self):
        """
        The host name of the proxy to use to deliver requests, if any
        """
        return self._proxy_host

    @proxy_host.setter  # type: ignore
    @validate_str_setter
    def proxy_host(self, value: str):
        self._proxy_host = value

    @property
    def release_stage(self):
        """
        The development phase of the deployed application. This value is used
        to differentiate events which occur in production vs development or
        staging environments.
        """
        return self._release_stage

    @release_stage.setter  # type: ignore
    @validate_str_setter
    def release_stage(self, value: str):
        self._release_stage = value

    @property
    def send_code(self):
        """
        If the source code lines immediately surrounding traceback locations
        should be sent with events
        """
        return self._send_code

    @send_code.setter  # type: ignore
    @validate_bool_setter
    def send_code(self, value: bool):
        self._send_code = value

    @property
    def send_environment(self):
        """
        If the request environment should be automatically collected and
        attached to events
        """
        return self._send_environment

    @send_environment.setter  # type: ignore
    @validate_bool_setter
    def send_environment(self, value: bool):
        self._send_environment = value

    @property
    def session_endpoint(self):
        """
        Sessions API endpoint. Set this property if using Bugsnag On-Premise.

        >>> config = Configuration()
        >>> config.session_endpoint = 'https://sessions.bugsnag.example.co'
        """
        return self._session_endpoint

    @session_endpoint.setter  # type: ignore
    @validate_required_str_setter
    def session_endpoint(self, value: str):
        self._session_endpoint = value

    @property
    def traceback_exclude_modules(self):
        """
        Modules which should be stripped from event tracebacks entirely
        """
        return self._traceback_exclude_modules

    @traceback_exclude_modules.setter  # type: ignore
    @validate_iterable_setter
    def traceback_exclude_modules(self, value: List[str]):
        self._traceback_exclude_modules = value

    @property
    def logger(self) -> logging.Logger:
        """
        Logger for use internally
        """
        return self._logger

    @logger.setter  # type: ignore
    def logger(self, logger: Optional[logging.Logger]) -> None:
        if logger is _sentinel:
            logger = self._create_default_logger()
        elif logger is None:
            logger = self._create_null_logger()

        if not isinstance(logger, logging.Logger):
            actual = type(logger).__name__
            message = 'logger should be logging.Logger, got ' + actual
            warnings.warn(message, RuntimeWarning)

            logger = self._create_default_logger()

        self._logger = logger

    @property
    def max_breadcrumbs(self) -> int:
        return self._max_breadcrumbs

    @max_breadcrumbs.setter  # type: ignore
    @validate_int_setter
    def max_breadcrumbs(self, new_max: int) -> None:
        if 0 <= new_max <= 100:
            self._breadcrumbs.resize(new_max)
            self._max_breadcrumbs = new_max
        else:
            message = (
                'max_breadcrumbs should be an int between 0 and 100, got "{}"'
            ).format(new_max)

            warnings.warn(message, RuntimeWarning)

    @property
    def breadcrumbs(self) -> List[Breadcrumb]:
        return self._breadcrumbs.to_list()

    def add_on_breadcrumb(self, on_breadcrumb: OnBreadcrumbCallback) -> None:
        with self._mutex:
            self._on_breadcrumbs.append(on_breadcrumb)

    def remove_on_breadcrumb(
        self,
        on_breadcrumb: OnBreadcrumbCallback
    ) -> None:
        with self._mutex:
            try:
                self._on_breadcrumbs.remove(on_breadcrumb)
            except ValueError:
                # ignore exception if "on_breadcrumb" is not in the list
                pass

    def should_notify(self) -> bool:
        return self.notify_release_stages is None or \
            (isinstance(self.notify_release_stages, (tuple, list)) and
             self.release_stage in self.notify_release_stages)

    def should_ignore(self, exception: BaseException) -> bool:
        return self.ignore_classes is not None and \
            fully_qualified_class_name(exception) in self.ignore_classes

    def _create_default_logger(self) -> logging.Logger:
        logger = logging.getLogger('bugsnag')
        logger.setLevel(logging.WARNING)

        format = '%(asctime)s - [%(name)s] %(levelname)s - %(message)s'
        formatter = logging.Formatter(format)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        return logger

    def _create_null_logger(self) -> logging.Logger:
        logger = logging.getLogger('bugsnag')
        logger.handlers = []

        logger.addHandler(logging.NullHandler())

        return logger


class RequestConfiguration:
    """
    Per-request Bugsnag configuration settings.
    """

    @classmethod
    def get_instance(cls):
        """
        Get this thread's instance of the RequestConfiguration.
        """

        try:
            instance = _request_info.get()
        except LookupError:
            instance = None

        if instance is None:
            instance = RequestConfiguration()
            _request_info.set(instance)  # type: ignore

        return instance

    @classmethod
    def clear(cls):
        """
        Clear this thread's instance of the RequestConfiguration.
        """
        _request_info.set(None)

    def __init__(self):
        self.context = None
        self.grouping_hash = None
        self.user = {}
        self.metadata = {}

        # legacy fields
        self.user_id = None
        self.extra_data = {}
        self.request_data = {}
        self.environment_data = {}
        self.session_data = {}

    def get(self, name) -> Any:
        """
        Get a single configuration option
        """
        return getattr(self, name)

    def configure(self, **options):
        """
        Set one or more configuration settings.
        """
        for name, value in options.items():
            setattr(self, name, value)

        return self

    @property
    def meta_data(self) -> Any:
        warnings.warn('RequestConfiguration.meta_data has been renamed to ' +
                      '"metadata"', DeprecationWarning)
        return self.metadata
