import bugsnag


class SimpleMiddleware(object):
    def __init__(self, before=None, after=None):
        self.before = before
        self.after = after

    def __call__(self, bugsnag):

        def middleware(notification):
            if self.before:
                ret = self.before(notification)
                if ret is False:
                    return

            bugsnag(notification)

            if self.after:
                self.after(notification)

        return middleware


class DefaultMiddleware(object):
    """
    DefaultMiddleware provides the transformation from request_config into
    meta-data that has always been supported by bugsnag-python.
    """
    def __init__(self, bugsnag):
        self.bugsnag = bugsnag

    def __call__(self, notification):
        config = notification.request_config
        notification.set_user(id=config.user_id)
        notification.set_user(**config.user)

        if not notification.context:
            notification.context = config.get("context")

        for name, dictionary in config.meta_data.items():
            if name in notification.meta_data:
                for key, value in dictionary.items():
                    if key not in notification.meta_data[name]:
                        notification.meta_data[name][key] = value
            else:
                notification.add_tab(name, dictionary)

        notification.add_tab("request", config.get("request_data"))
        notification.add_tab("environment", config.get("environment_data"))
        notification.add_tab("session", config.get("session_data"))
        notification.add_tab("extraData", config.get("extra_data"))

        self.bugsnag(notification)


class MiddlewareStack(object):
    """
    Manages a stack of Bugsnag middleware.
    """
    def __init__(self):
        self.stack = []

    def before_notify(self, func):
        """
        Add a function to be run before bugsnag is notified.

        This lets you modify the payload that will be sent.
        If your function returns False, nothing will be sent.

        >>> def add_request_data(notification):
        ...    notification.add_tab("request", request_data)
        ...
        ... bugsnag.middleware.before_notify(add_request_data)
        """
        self.append(SimpleMiddleware(before=func))

    def after_notify(self, func):
        """
        Add a function to be run after bugsnag is notified.

        This lets you log errors in custom ways.
        """
        self.append(SimpleMiddleware(after=func))

    def append(self, middleware):
        """
        Add a middleware to the end of the stack.

        It will be run after all middleware currently defined.
        If you want to stop the notification progress, return from
        your __call__ method without calling the next level.

        >>> class ExampleMiddleware():
        ...     def __init__(self, bugsnag):
        ...         self.bugsnag = bugsnag
        ...
        ...     def __call__(self, notification):
        ...         config = notification.request_config
        ...         notification.add_tab("request", config.get("request")))
        ...         self.bugsnag(notification)
        ...
        >>> bugsnag.middleware.append(ExampleMiddleware)
        """
        self.stack.append(middleware)

    def insert_before(self, target_class, middleware):
        """
        Adds a middleware to the stack in the position before
        the target_class.
        """
        try:
            index = self.stack.index(target_class)
            self.stack.insert(index, middleware)
        except ValueError:
            self.append(middleware)

    def insert_after(self, target_class, middleware):
        """
        Adds a middleware to the stack in the position after
        the target_class.
        """
        try:
            index = self.stack.index(target_class)
            self.stack.insert(index + 1, middleware)
        except ValueError:
            self.append(middleware)

    def run(self, notification, callback):
        """
        Run all the middleware in order, then call the callback.
        """

        # the last step in the notification stack is to call the callback.
        # we also do this inside the exception handler, so need to ensure that
        # the callback is only called once.
        def finish(notification):
            if not hasattr(finish, 'called'):
                finish.called = True
                callback()

        to_call = finish
        for middleware in reversed(self.stack):
            to_call = middleware(to_call)

        try:
            to_call(notification)
        except Exception:
            bugsnag.logger.exception('Error in exception middleware')
            # still notify if middleware crashes before notification
            finish(notification)
