from distutils.sysconfig import get_python_lib
import threading


threadlocal = threading.local()

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
            if hasattr(self, name):
                setattr(self, name, value)

class Configuration(_BaseConfiguration):
    """
    Global app-level Bugsnag configuration settings.
    """
    def __init__(self):
        self.api_key = None
        self.release_stage = "production"
        self.notify_release_stages = ["production"]
        self.auto_notify = True
        self.use_ssl = False
        self.lib_root = get_python_lib()
        self.project_root = None
        self.app_version = None
        self.params_filters = ["password", "password_confirmation"]
        self.ignore_classes = None # TODO:JS
        self.endpoint = "notify.bugsnag.com"


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
        self.user_id = None
        self.extra_data = {}
        self.request_data = {}
        self.environment_data = {}
        self.session_data = {}