import sys

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification


__all__ = ('Client',)


class Client(object):
    """
    A Bugsnag monitoring and reporting client.

    >>> client = Client(api_key='...')
    """

    def __init__(self, configuration=None, install_sys_hook=True, **kwargs):
        self.configuration = configuration or Configuration()
        self.configuration.configure(**kwargs)

        if install_sys_hook:
            self.install_sys_hook()

    def context(self, swallow=True, **options):
        """
        Run a block of code within the clients context.
        Any exception raised will be reported to bugsnag.

        The `swallow` option allows you to tell the context to provide the
        exception back to the caller.

        >>> with client.context():
        >>>     raise Exception('an exception passed to bugsnag')
        """
        return ClientContext(self, swallow, **options)

    def notify(self, exception, **options):
        """
        Notify bugsnag of an exception.

        >>> client.notify(Exception('Example'))
        """

        notification = Notification(exception, self.configuration,
                                    RequestConfiguration.get_instance(),
                                    **options)
        notification.deliver()


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
        notification.deliver()

    def excepthook(self, exc_type, exc_value, traceback):
        if self.configuration.auto_notify:
            self.notify_exc_info(exc_type, exc_value, traceback,
                                 severity='error')

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


class ClientContext(object):
    def __init__(self, client, swallow, **options):
        self.client = client
        self.swallow = swallow
        self.options = options

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        if any(exc_info):
            self.client.notify_exc_info(*exc_info, **self.options)

        return self.swallow
