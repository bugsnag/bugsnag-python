import bugsnag


class SimpleMiddleware(object):
    def __init__(self, before=None, after=None):
        self.before = before
        self.after = after

    def __call__(self, bugsnag):

        def middleware(event):
            if self.before:
                ret = self.before(event)
                if ret is False:
                    return

            bugsnag(event)

            if self.after:
                self.after(event)

        return middleware


class DefaultMiddleware(object):
    """
    DefaultMiddleware provides the transformation from request_config into
    meta-data that has always been supported by bugsnag-python.
    """
    def __init__(self, bugsnag):
        self.bugsnag = bugsnag

    def __call__(self, event):
        config = event.request_config
        event.set_user(id=config.user_id)
        event.set_user(**config.user)

        if not event.context:
            event.context = config.get("context")

        for name, dictionary in config.meta_data.items():
            if name in event.meta_data:
                for key, value in dictionary.items():
                    if key not in event.meta_data[name]:
                        event.meta_data[name][key] = value
            else:
                event.add_tab(name, dictionary)

        event.add_tab("request", config.get("request_data"))
        if bugsnag.configure().send_environment:
            event.add_tab("environment", config.get("environment_data"))
        event.add_tab("session", config.get("session_data"))
        event.add_tab("extraData", config.get("extra_data"))

        self.bugsnag(event)


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

        >>> def add_request_data(event):
        ...    event.add_tab("request", request_data)
        >>>
        >>> stack = MiddlewareStack()
        >>> stack.before_notify(add_request_data)
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
        If you want to stop the event progress, return from
        your __call__ method without calling the next level.

        >>> class ExampleMiddleware():
        ...     def __init__(self, bugsnag):
        ...         self.bugsnag = bugsnag
        ...     def __call__(self, event):
        ...         config = event.request_config
        ...         event.add_tab("request", config.get("request"))
        ...         self.bugsnag(event)
        ...
        >>> stack = MiddlewareStack()
        >>> stack.append(ExampleMiddleware)
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

    def run(self, event, callback):
        """
        Run all the middleware in order, then call the callback.
        """

        # the last step in the event stack is to call the callback.
        # we also do this inside the exception handler, so need to ensure that
        # the callback is only called once.
        def finish(event):
            if not hasattr(finish, 'called'):
                finish.called = True
                callback()

        to_call = finish
        for middleware in reversed(self.stack):
            to_call = middleware(to_call)

        try:
            to_call(event)
        except Exception:
            bugsnag.logger.exception('Error in exception middleware')
            # still notify if middleware crashes before event
            finish(event)
