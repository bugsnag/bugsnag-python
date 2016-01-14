from webtest import TestApp
from nose.tools import eq_, assert_raises
from mock import patch

from bugsnag.wsgi.middleware import BugsnagMiddleware
from six import Iterator
import bugsnag.notification


bugsnag.configuration.api_key = '066f5ad3590596f9aa8d601ea89af845'


class SentinalError(RuntimeError):
    pass


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_working(deliver):
    def BasicWorkingApp(environ, start_response):
        start_response("200 OK",
                       [('Content-Type', 'text/plain; charset=utf-8')])
        return iter([b'OK'])

    app = TestApp(BugsnagMiddleware(BasicWorkingApp))

    resp = app.get('/', status=200)
    eq_(resp.body, b'OK')

    eq_(deliver.call_count, 0)


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_crash_on_start(deliver):

    class CrashOnStartApp(object):
        def __init__(self, environ, start_response):
            raise SentinalError("oops")

    app = TestApp(BugsnagMiddleware(CrashOnStartApp))

    assert_raises(SentinalError, lambda: app.get('/beans'))

    eq_(deliver.call_count, 1)
    payload = deliver.call_args[0][0]
    eq_(payload['events'][0]['context'], 'GET /beans')
    eq_(payload['events'][0]['metaData']['environment']['PATH_INFO'], '/beans')


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_crash_on_iter(deliver):
    class CrashOnIterApp(Iterator):
        def __init__(self, environ, start_response):
            pass

        def __iter__(self):
            return self

        def __next__(self):
            raise SentinalError("oops")
    app = TestApp(BugsnagMiddleware(CrashOnIterApp))

    assert_raises(SentinalError, lambda: app.get('/beans'))

    eq_(deliver.call_count, 1)
    payload = deliver.call_args[0][0]
    eq_(payload['events'][0]['metaData']['environment']['PATH_INFO'], '/beans')


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_crash_on_close(deliver):
    class CrashOnCloseApp(Iterator):
        def __init__(self, environ, start_response):
            pass

        def __iter__(self):
            return self

        def __next__(self):
            raise StopIteration()

        def close(self):
            raise SentinalError("oops")

    app = TestApp(BugsnagMiddleware(CrashOnCloseApp))

    assert_raises(SentinalError, lambda: app.get('/beans'))

    eq_(deliver.call_count, 1)
    payload = deliver.call_args[0][0]
    eq_(payload['events'][0]['metaData']['environment']['PATH_INFO'], '/beans')


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_respects_user_id(deliver):

    class CrashAfterSettingUserId(object):
        def __init__(self, environ, start_response):
            bugsnag.configure_request(user={"id": "5", "email":
                                            "me@cirw.in", "name": "conrad"})
            raise SentinalError("oops")

    app = TestApp(BugsnagMiddleware(CrashAfterSettingUserId))

    assert_raises(SentinalError, lambda: app.get('/beans'))

    eq_(deliver.call_count, 1)
    payload = deliver.call_args[0][0]
    eq_(payload['events'][0]['user']['id'], '5')


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_respects_meta_data(deliver):

    class CrashAfterSettingMetaData(object):
        def __init__(self, environ, start_response):
            bugsnag.configure_request(meta_data={"account": {"paying": True}})

        def __iter__(self):
            raise SentinalError("oops")

    app = TestApp(BugsnagMiddleware(CrashAfterSettingMetaData))

    assert_raises(SentinalError, lambda: app.get('/beans'))

    eq_(deliver.call_count, 1)
    payload = deliver.call_args[0][0]
    eq_(payload['events'][0]['metaData']['account'], {"paying": True})


@patch('bugsnag.notification.deliver')
def test_bugsnag_middleware_closes_iterables(deliver):

    class CrashOnCloseIterable(object):

        def __init__(self, environ, start_response):
            start_response("200 OK",
                           [('Content-Type', 'text/plain; charset=utf-8')])

        def __iter__(self):
            yield 'OK'

        def close(self):
            raise SentinalError("oops")

    app = TestApp(BugsnagMiddleware(CrashOnCloseIterable))

    assert_raises(SentinalError, lambda: app.get('/beans'))

    eq_(deliver.call_count, 1)
    payload = deliver.call_args[0][0]
    eq_(payload['events'][0]['metaData']['environment']['PATH_INFO'], '/beans')
