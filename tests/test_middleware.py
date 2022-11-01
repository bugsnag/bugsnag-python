import unittest

import bugsnag
from bugsnag.middleware import MiddlewareStack, skip_bugsnag_middleware
from bugsnag.configuration import RequestConfiguration


class SampleMiddlewareClass(object):
    def __init__(self, callback):
        self.callback = callback
        self.char = None

    def __call__(self, item):
        item.append(self.char)
        self.callback(item)


class SampleMiddlewareClassA(SampleMiddlewareClass):
    def __init__(self, callback):
        SampleMiddlewareClass.__init__(self, callback)
        self.char = 'A'


class SampleMiddlewareClassB(SampleMiddlewareClass):
    def __init__(self, callback):
        SampleMiddlewareClass.__init__(self, callback)
        self.char = 'B'


class SampleMiddlewareClassC(SampleMiddlewareClass):
    def __init__(self, callback):
        SampleMiddlewareClass.__init__(self, callback)
        self.char = 'C'


class SampleMiddlewareReturning(object):
    def __init__(self, callback):
        pass

    def __call__(self, item):
        return


def create_event(exception=None) -> bugsnag.Event:
    return bugsnag.Event(
        exception or RuntimeError('oh no!'),
        bugsnag.configure(),
        RequestConfiguration.get_instance()
    )


class TestMiddleware(unittest.TestCase):

    def test_order_of_middleware(self):

        a = []

        m = MiddlewareStack()

        m.before_notify(lambda _: a.append(1))
        m.before_notify(lambda _: a.append(2))

        m.after_notify(lambda _: a.append(4))
        m.after_notify(lambda _: a.append(3))

        m.run(create_event(), lambda: None)

        self.assertEqual(a, [1, 2, 3, 4])

    def test_before_notify_returning_false(self):

        a = []

        m = MiddlewareStack()

        m.before_notify(lambda _: False)
        m.before_notify(lambda _: a.append(1))

        m.run(create_event(), lambda: a.append(2))

        self.assertEqual(a, [])

    def test_before_exception_handling(self):

        a = []

        m = MiddlewareStack()
        m.before_notify(lambda _: a.penned(1))
        m.run(create_event(), lambda: a.append(2))

        self.assertEqual(a, [2])

    def test_after_exception_handling(self):
        a = []

        m = MiddlewareStack()
        m.after_notify(lambda _: a.penned(1))
        m.run(create_event(), lambda: a.append(2))

        self.assertEqual(a, [2])

    def test_insert_before_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(SampleMiddlewareClassA)
        m.append(SampleMiddlewareClassB)
        m.insert_before(SampleMiddlewareClassA, SampleMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['C', 'A', 'B', 'Callback'])

    def test_insert_before_default_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(SampleMiddlewareClassA)
        m.append(SampleMiddlewareClassB)
        m.insert_before(SampleMiddlewareClass, SampleMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A', 'B', 'C', 'Callback'])

    def test_insert_after_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(SampleMiddlewareClassA)
        m.append(SampleMiddlewareClassB)
        m.insert_after(SampleMiddlewareClassA, SampleMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A', 'C', 'B', 'Callback'])

    def test_insert_after_default_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(SampleMiddlewareClassA)
        m.append(SampleMiddlewareClassB)
        m.insert_after(SampleMiddlewareClass, SampleMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A', 'B', 'C', 'Callback'])

    def test_callback_not_run_if_middleware_returns(self):
        a = []

        m = MiddlewareStack()
        m.append(SampleMiddlewareClassA)
        m.append(SampleMiddlewareReturning)
        m.append(SampleMiddlewareClassB)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A'])

    def test_skip_bugsnag_middleware_returns_false_when_attr_is_present(self):
        exception = Exception('oh no')
        exception.skip_bugsnag = True

        event = create_event(exception)

        assert skip_bugsnag_middleware(event) is False

    def test_skip_bugsnag_middleware_returns_none_when_attr_is_missing(self):
        exception = Exception('oh no')
        event = create_event(exception)

        assert skip_bugsnag_middleware(event) is None
