import unittest

from bugsnag.middleware import MiddlewareStack


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
