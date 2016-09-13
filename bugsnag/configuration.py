from __future__ import absolute_import, division, print_function

import os
import socket
import threading
import warnings
from distutils.sysconfig import get_python_lib

from bugsnag.middleware import DefaultMiddleware, MiddlewareStack
from bugsnag.utils import fully_qualified_class_name
from bugsnag.delivery import create_default_delivery


threadlocal = threading.local()


class _BaseConfiguration(object):
    def get(self, name, overrides=None):
        """
        Get a single configuration option, using values from overrides
        first if they exist.
        """
        if name is 'use_ssl':
            warnings.warn('use_ssl is deprecated in favor of including the '
                          'protocol in the endpoint property and will be '
                          'removed in a future release',
                          DeprecationWarning)

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
        self.asynchronous = True
        self.use_ssl = True  # Deprecated
        self.delivery = create_default_delivery()
        self.lib_root = get_python_lib()
        self.project_root = os.getcwd()
        self.app_version = None
        self.params_filters = ["password", "password_confirmation", "cookie",
                               "authorization"]
        self.ignore_classes = ["KeyboardInterrupt", "django.http.Http404"]
        self.endpoint = "https://notify.bugsnag.com"
        self.traceback_exclude_modules = []

        self.middleware = MiddlewareStack()
        self.middleware.append(DefaultMiddleware)

        self.proxy_host = None

        if not os.getenv("DYNO"):
            self.hostname = socket.gethostname()
        else:
            self.hostname = None

    def should_notify(self):
        return self.notify_release_stages is None or \
            (isinstance(self.notify_release_stages, (tuple, list)) and
             self.release_stage in self.notify_release_stages)

    def should_ignore(self, exception):
        return self.ignore_classes is not None and \
            fully_qualified_class_name(exception) in self.ignore_classes

    def get_endpoint(self):
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
    def get_instance(cls):
        """
        Get this thread's instance of the RequestConfiguration.
        """
        instance = getattr(threadlocal, "bugsnag", None)
        if not instance:
            instance = RequestConfiguration()
            setattr(threadlocal, "bugsnag", instance)

        return instance

    @classmethod
    def clear(cls):
        """
        Clear this thread's instance of the RequestConfiguration.
        """
        if hasattr(threadlocal, "bugsnag"):
            delattr(threadlocal, "bugsnag")

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
