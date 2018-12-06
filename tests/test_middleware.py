import unittest

from bugsnag.middleware import MiddlewareStack


class TestMiddlewareClass(object):
    def __init__(self, callback):
        self.callback = callback
        self.char = None

    def __call__(self, item):
        item.append(self.char)
        self.callback(item)


class TestMiddlewareClassA(TestMiddlewareClass):
    def __init__(self, callback):
        TestMiddlewareClass.__init__(self, callback)
        self.char = 'A'


class TestMiddlewareClassB(TestMiddlewareClass):
    def __init__(self, callback):
        TestMiddlewareClass.__init__(self, callback)
        self.char = 'B'


class TestMiddlewareClassC(TestMiddlewareClass):
    def __init__(self, callback):
        TestMiddlewareClass.__init__(self, callback)
        self.char = 'C'


class TestMiddlewareReturning(object):
    def __init__(self, callback):
        pass

    def __call__(self, item):
        return


class TestMiddleware(unittest.TestCase):

    def test_order_of_middleware(self):

        a = []

        m = MiddlewareStack()

        m.before_notify(lambda _: a.append(1))
        m.before_notify(lambda _: a.append(2))

        m.after_notify(lambda _: a.append(4))
        m.after_notify(lambda _: a.append(3))

        m.run(None, lambda: None)

        self.assertEqual(a, [1, 2, 3, 4])

    def test_before_notify_returning_false(self):

        a = []

        m = MiddlewareStack()

        m.before_notify(lambda _: False)
        m.before_notify(lambda _: a.append(1))

        m.run(None, lambda: a.append(2))

        self.assertEqual(a, [])

    def test_before_exception_handling(self):

        a = []

        m = MiddlewareStack()
        m.before_notify(lambda _: a.penned(1))
        m.run(None, lambda: a.append(2))

        self.assertEqual(a, [2])

    def test_after_exception_handling(self):
        a = []

        m = MiddlewareStack()
        m.after_notify(lambda _: a.penned(1))
        m.run(None, lambda: a.append(2))

        self.assertEqual(a, [2])

    def test_insert_before_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(TestMiddlewareClassA)
        m.append(TestMiddlewareClassB)
        m.insert_before(TestMiddlewareClassA, TestMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['C', 'A', 'B', 'Callback'])

    def test_insert_before_default_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(TestMiddlewareClassA)
        m.append(TestMiddlewareClassB)
        m.insert_before(TestMiddlewareClass, TestMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A', 'B', 'C', 'Callback'])

    def test_insert_after_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(TestMiddlewareClassA)
        m.append(TestMiddlewareClassB)
        m.insert_after(TestMiddlewareClassA, TestMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A', 'C', 'B', 'Callback'])

    def test_insert_after_default_ordering(self):
        a = []

        m = MiddlewareStack()
        m.append(TestMiddlewareClassA)
        m.append(TestMiddlewareClassB)
        m.insert_after(TestMiddlewareClass, TestMiddlewareClassC)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A', 'B', 'C', 'Callback'])

    def test_callback_not_run_if_middleware_returns(self):
        a = []

        m = MiddlewareStack()
        m.append(TestMiddlewareClassA)
        m.append(TestMiddlewareReturning)
        m.append(TestMiddlewareClassB)
        m.run(a, lambda: a.append('Callback'))

        self.assertEqual(a, ['A'])
