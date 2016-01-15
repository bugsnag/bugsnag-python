import unittest

from webtest import TestApp
from mock import patch

from bugsnag.wsgi.middleware import BugsnagMiddleware
from six import Iterator
import bugsnag.notification


bugsnag.configuration.api_key = '066f5ad3590596f9aa8d601ea89af845'


class SentinelError(RuntimeError):
    pass


class TestWSGI(unittest.TestCase):

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_working(self, deliver):
        def BasicWorkingApp(environ, start_response):
            start_response("200 OK",
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return iter([b'OK'])

        app = TestApp(BugsnagMiddleware(BasicWorkingApp))

        resp = app.get('/', status=200)
        self.assertEqual(resp.body, b'OK')

        self.assertEqual(deliver.call_count, 0)

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_crash_on_start(self, deliver):

        class CrashOnStartApp(object):
            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnStartApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(deliver.call_count, 1)
        payload = deliver.call_args[0][0]
        event = payload['events'][0]
        self.assertEqual(event['context'], 'GET /beans')
        self.assertEqual(event['metaData']['environment']['PATH_INFO'],
                         '/beans')

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_crash_on_iter(self, deliver):
        class CrashOnIterApp(Iterator):
            def __init__(self, environ, start_response):
                pass

            def __iter__(self):
                return self

            def __next__(self):
                raise SentinelError("oops")
        app = TestApp(BugsnagMiddleware(CrashOnIterApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(deliver.call_count, 1)
        payload = deliver.call_args[0][0]
        environ = payload['events'][0]['metaData']['environment']
        self.assertEqual(environ['PATH_INFO'], '/beans')

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_crash_on_close(self, deliver):
        class CrashOnCloseApp(Iterator):
            def __init__(self, environ, start_response):
                pass

            def __iter__(self):
                return self

            def __next__(self):
                raise StopIteration()

            def close(self):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnCloseApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(deliver.call_count, 1)
        payload = deliver.call_args[0][0]
        environ = payload['events'][0]['metaData']['environment']
        self.assertEqual(environ['PATH_INFO'], '/beans')

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_respects_user_id(self, deliver):

        class CrashAfterSettingUserId(object):
            def __init__(self, environ, start_response):
                bugsnag.configure_request(
                        user={"id": "5", "email":
                              "me@cirw.in", "name": "conrad"})
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashAfterSettingUserId))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(deliver.call_count, 1)
        payload = deliver.call_args[0][0]
        self.assertEqual(payload['events'][0]['user']['id'], '5')

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_respects_meta_data(self, deliver):

        class CrashAfterSettingMetaData(object):
            def __init__(self, environ, start_response):
                bugsnag.configure_request(meta_data={"account":
                                                     {"paying": True}})

            def __iter__(self):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashAfterSettingMetaData))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(deliver.call_count, 1)
        payload = deliver.call_args[0][0]
        event = payload['events'][0]
        self.assertEqual(event['metaData']['account'], {"paying": True})

    @patch('bugsnag.notification.deliver')
    def test_bugsnag_middleware_closes_iterables(self, deliver):

        class CrashOnCloseIterable(object):

            def __init__(self, environ, start_response):
                start_response("200 OK",
                               [('Content-Type', 'text/plain; charset=utf-8')])

            def __iter__(self):
                yield 'OK'

            def close(self):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnCloseIterable))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(deliver.call_count, 1)
        payload = deliver.call_args[0][0]
        environ = payload['events'][0]['metaData']['environment']
        self.assertEqual(environ['PATH_INFO'], '/beans')
