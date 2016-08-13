import unittest

from webtest import TestApp

from bugsnag.wsgi.middleware import BugsnagMiddleware
from six import Iterator
import bugsnag.notification
import bugsnag
from tests.utils import FakeBugsnagServer


class SentinelError(RuntimeError):
    pass


class TestWSGI(unittest.TestCase):

    def setUp(self):
        self.server = FakeBugsnagServer(5858)
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.url(),
                          api_key='3874876376238728937',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          async=False)

    def shutDown(self):
        bugsnag.configuration = bugsnag.Configuration()
        bugsnag.configuration.api_key = 'some key'

    def test_bugsnag_middleware_working(self):
        def BasicWorkingApp(environ, start_response):
            start_response("200 OK",
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return iter([b'OK'])

        app = TestApp(BugsnagMiddleware(BasicWorkingApp))

        resp = app.get('/', status=200)
        self.server.shutdown()
        self.assertEqual(resp.body, b'OK')

        self.assertEqual(0, len(self.server.received))

    def test_bugsnag_middleware_crash_on_start(self):

        class CrashOnStartApp(object):
            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnStartApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['context'], 'GET /beans')
        self.assertEqual(event['metaData']['environment']['PATH_INFO'],
                         '/beans')

    def test_bugsnag_middleware_crash_on_iter(self):
        class CrashOnIterApp(Iterator):
            def __init__(self, environ, start_response):
                pass

            def __iter__(self):
                return self

            def __next__(self):
                raise SentinelError("oops")
        app = TestApp(BugsnagMiddleware(CrashOnIterApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        environ = payload['events'][0]['metaData']['environment']
        self.assertEqual(environ['PATH_INFO'], '/beans')

    def test_bugsnag_middleware_crash_on_close(self):
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
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        environ = payload['events'][0]['metaData']['environment']
        self.assertEqual(environ['PATH_INFO'], '/beans')

    def test_bugsnag_middleware_respects_user_id(self):

        class CrashAfterSettingUserId(object):
            def __init__(self, environ, start_response):
                bugsnag.configure_request(
                        user={"id": "5", "email":
                              "me@cirw.in", "name": "conrad"})
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashAfterSettingUserId))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        self.assertEqual(payload['events'][0]['user']['id'], '5')

    def test_bugsnag_middleware_respects_meta_data(self):

        class CrashAfterSettingMetaData(object):
            def __init__(self, environ, start_response):
                bugsnag.configure_request(meta_data={"account":
                                                     {"paying": True}})

            def __iter__(self):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashAfterSettingMetaData))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['account'], {"paying": True})

    def test_bugsnag_middleware_closes_iterables(self):

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
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        environ = payload['events'][0]['metaData']['environment']
        self.assertEqual(environ['PATH_INFO'], '/beans')
