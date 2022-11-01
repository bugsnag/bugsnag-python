from typing import Callable, Optional, Type, List

from bugsnag.event import Event


Middleware = Callable[[Event], Callable]


__all__ = []  # type: List[str]


class SimpleMiddleware:
    def __init__(self, before: Optional[Middleware] = None,
                 after: Optional[Middleware] = None):
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


class DefaultMiddleware:
    """
    DefaultMiddleware provides the transformation from request_config into
    metadata that has always been supported by bugsnag-python.
    """
    def __init__(self, bugsnag: Middleware):
        self.bugsnag = bugsnag

    def __call__(self, event: Event):
        config = event.request_config
        event.set_user(id=config.user_id)
        event.set_user(**config.user)

        if not event.context:
            event.context = config.get("context")

        for name, dictionary in config.metadata.items():
            if name in event.metadata:
                for key, value in dictionary.items():
                    if key not in event.metadata[name]:
                        event.metadata[name][key] = value
            else:
                event.add_tab(name, dictionary)

        event.add_tab("request", config.get("request_data"))
        if event.config.send_environment:
            event.add_tab("environment", config.get("environment_data"))
        event.add_tab("session", config.get("session_data"))
        event.add_tab("extraData", config.get("extra_data"))

        self.bugsnag(event)


def skip_bugsnag_middleware(event: Event):
    """
    A callback-based middleware that prevents notifying an event where the
    'original_error' has a 'skip_bugsnag' attr set to 'True'.
    """
    if getattr(event.original_error, 'skip_bugsnag', False) is True:
        return False


class MiddlewareStack:
    """
    Manages a stack of Bugsnag middleware.
    """
    def __init__(self):
        self.stack = []

    def before_notify(self, func: Middleware):
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

    def after_notify(self, func: Middleware):
        """
        Add a function to be run after bugsnag is notified.

        This lets you log errors in custom ways.
        """
        self.append(SimpleMiddleware(after=func))

    def append(self, middleware: Middleware):
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

    def insert_before(self, target_class: Type, middleware: Middleware):
        """
        Adds a middleware to the stack in the position before
        the target_class.
        """
        try:
            index = self.stack.index(target_class)
            self.stack.insert(index, middleware)
        except ValueError:
            self.append(middleware)

    def insert_after(self, target_class: Type, middleware: Middleware):
        """
        Adds a middleware to the stack in the position after
        the target_class.
        """
        try:
            index = self.stack.index(target_class)
            self.stack.insert(index + 1, middleware)
        except ValueError:
            self.append(middleware)

    def run(self, event: Event, callback: Callable[[], None]):
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
            event.config.logger.exception(
                'Error in exception middleware'
            )

            # still notify if middleware crashes before event
            finish(event)
