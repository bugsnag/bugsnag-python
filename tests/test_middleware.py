import os
import socket

from nose.tools import eq_

from bugsnag.middleware import MiddlewareStack


def test_order_of_middleware():

    a = []

    m = MiddlewareStack()

    m.before_notify(lambda _: a.append(1))
    m.before_notify(lambda _: a.append(2))

    m.after_notify(lambda _: a.append(4))
    m.after_notify(lambda _: a.append(3))

    m.run(None, lambda: None)

    eq_(a, [1,2,3,4])

def test_before_notify_returning_false():

    a = []

    m = MiddlewareStack()

    m.before_notify(lambda _: False)
    m.before_notify(lambda _: a.append(1))

    m.run(None, lambda: a.append(2))

    eq_(a, [])

def test_before_exception_handling():

    a = []

    m = MiddlewareStack()
    m.before_notify(lambda _: a.penned(1))
    m.run(None, lambda: a.append(2))

    eq_(a, [2])

def test_after_exception_handling():
    a = []

    m = MiddlewareStack()
    m.after_notify(lambda _: a.penned(1))
    m.run(None, lambda: a.append(2))

    eq_(a, [2])
