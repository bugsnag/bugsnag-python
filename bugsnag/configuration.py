from __future__ import absolute_import, division, print_function

import os
import platform
import socket
try:
    import sysconfig

    def get_python_lib(): sysconfig.get_path('purelib')
except ImportError:
    # Compatibility with Python 2.6
    from distutils.sysconfig import get_python_lib
import warnings

from bugsnag.sessiontracker import SessionMiddleware
from bugsnag.middleware import DefaultMiddleware, MiddlewareStack
from bugsnag.utils import (fully_qualified_class_name, validate_str_setter,
                           validate_bool_setter, validate_iterable_setter,
                           validate_required_str_setter)
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


class _BaseConfiguration(object):
    def get(self, name, overrides=None):
        """
        Get a single configuration option, using values from overrides
        first if they exist.
        """
        if overrides:
            return overrides.get(name, getattr(self, name))
        else:
            return getattr(self, name)

    def configure(self, **options):
        """
        Set one or more configuration settings.
        """
        for name, value in options.items():
            setattr(self, name, value)

        return self


class Configuration(_BaseConfiguration):
    """
    Global app-level Bugsnag configuration settings.
    """
    def __init__(self):
        self.api_key = os.environ.get('BUGSNAG_API_KEY', None)
        self.release_stage = os.environ.get("BUGSNAG_RELEASE_STAGE",
                                            "production")
        self.notify_release_stages = None
        self.auto_notify = True
        self.send_code = True
        self.send_environment = True
        self.asynchronous = True
        self.use_ssl = True  # Deprecated
        self.delivery = create_default_delivery()
        self.lib_root = get_python_lib()
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

    def configure(self, **options):
        """
        Validate and set configuration options. Will warn if an option is of an
        incorrect type.
        """
        # Overrides the default implementation to provide warnings for unknown
        # options. In the __future__ this will not be necessary by instead
        # making configure() enumerate all of the options as kwargs rather than
        # allowing arbitrary input.
        configurable_options = [
            'api_key', 'app_version', 'asynchronous', 'auto_notify',
            'auto_capture_sessions', 'delivery', 'endpoint', 'hostname',
            'ignore_classes', 'lib_root', 'notify_release_stages',
            'params_filters', 'project_root', 'proxy_host', 'release_stage',
            'send_code', 'session_endpoint', 'traceback_exclude_modules',
            'use_ssl', 'app_type', 'send_environment',
        ]

        for option_name in options.keys():
            if option_name not in configurable_options:
                message = 'received unknown configuration option "{0}"'
                warnings.warn(message.format(option_name), RuntimeWarning)
            setattr(self, option_name, options.get(option_name))

        return self

    @property
    def api_key(self):
        """
        Unique application identifier
        """
        return self._api_key

    @api_key.setter  # type: ignore
    @validate_required_str_setter
    def api_key(self, value):
        self._api_key = value

    @property
    def app_type(self):
        """
        Category for the current application or task
        """
        return self._app_type

    @app_type.setter  # type: ignore
    @validate_str_setter
    def app_type(self, value):
        self._app_type = value

    @property
    def app_version(self):
        """
        Release version of the current application
        """
        return self._app_version

    @app_version.setter  # type: ignore
    @validate_str_setter
    def app_version(self, value):
        self._app_version = value

    @property
    def asynchronous(self):
        """
        If API requests should be sent asynchronously
        """
        return self._asynchronous

    @asynchronous.setter  # type: ignore
    @validate_bool_setter
    def asynchronous(self, value):
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
    def auto_capture_sessions(self, value):
        self._auto_capture_sessions = value

    @property
    def auto_notify(self):
        """
        If uncaught exceptions should be automatically captured and reported
        """
        return self._auto_notify

    @auto_notify.setter  # type: ignore
    @validate_bool_setter
    def auto_notify(self, value):
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
    def endpoint(self, value):
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
    def hostname(self, value):
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
    def ignore_classes(self, value):
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
    def lib_root(self, value):
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
    def notify_release_stages(self, value):
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
    def params_filters(self, value):
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
    def project_root(self, value):
        self._project_root = value

    @property
    def proxy_host(self):
        """
        The host name of the proxy to use to deliver requests, if any
        """
        return self._proxy_host

    @proxy_host.setter  # type: ignore
    @validate_str_setter
    def proxy_host(self, value):
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
    def release_stage(self, value):
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
    def send_code(self, value):
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
    def send_environment(self, value):
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
    def session_endpoint(self, value):
        self._session_endpoint = value

    @property
    def traceback_exclude_modules(self):
        """
        Modules which should be stripped from event tracebacks entirely
        """
        return self._traceback_exclude_modules

    @traceback_exclude_modules.setter  # type: ignore
    @validate_iterable_setter
    def traceback_exclude_modules(self, value):
        self._traceback_exclude_modules = value

    @property
    def use_ssl(self):
        """
        This property is used to determine the protocol of endpoint and is
        deprecated in favor of including the protocol in the endpoint property.
        """
        return self._use_ssl

    @use_ssl.setter  # type: ignore
    @validate_bool_setter
    def use_ssl(self, value):
        warnings.warn('use_ssl is deprecated in favor of including the '
                      'protocol in the endpoint property and will be removed '
                      'in a future release', DeprecationWarning)
        self._use_ssl = value

    def should_notify(self):  # type: () -> bool
        return self.notify_release_stages is None or \
            (isinstance(self.notify_release_stages, (tuple, list)) and
             self.release_stage in self.notify_release_stages)

    def should_ignore(self, exception):  # type: (Exception) -> bool
        return self.ignore_classes is not None and \
            fully_qualified_class_name(exception) in self.ignore_classes

    def get_endpoint(self):  # type: () -> str
        warnings.warn('get_endpoint and use_ssl are deprecated in favor '
                      'of including the protocol in the endpoint '
                      'configuration option and will be removed in a future '
                      'release', DeprecationWarning)

        def format_endpoint(endpoint):
            proto = "https" if self.use_ssl is True else "http"
            return "%s://%s" % (proto, endpoint)

        if '://' not in self.endpoint:
            return format_endpoint(self.endpoint)
        elif self.use_ssl is not None:
            return format_endpoint(self.endpoint.split('://')[1])

        return self.endpoint


class RequestConfiguration(_BaseConfiguration):
    """
    Per-request Bugsnag configuration settings.
    """

    @classmethod
    def get_instance(cls):  # type: () -> RequestConfiguration
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
        self.meta_data = {}

        # legacy fields
        self.user_id = None
        self.extra_data = {}
        self.request_data = {}
        self.environment_data = {}
        self.session_data = {}
