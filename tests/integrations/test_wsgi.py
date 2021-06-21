import pytest
from webtest import TestApp

from bugsnag.wsgi.middleware import BugsnagMiddleware
import bugsnag.event
import bugsnag
from bugsnag.breadcrumbs import BreadcrumbType
from tests.utils import IntegrationTest


class SentinelError(RuntimeError):
    pass


class TestWSGI(IntegrationTest):

    def setUp(self):
        super(TestWSGI, self).setUp()
        bugsnag.configure(endpoint=self.server.url,
                          api_key='3874876376238728937',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          asynchronous=False,
                          max_breadcrumbs=25)

    def test_bugsnag_middleware_working(self):
        def BasicWorkingApp(environ, start_response):
            start_response("200 OK",
                           [('Content-Type', 'text/plain; charset=utf-8')])
            return iter([b'OK'])

        app = TestApp(BugsnagMiddleware(BasicWorkingApp))

        resp = app.get('/', status=200)

        self.assertEqual(resp.body, b'OK')
        self.assertEqual(0, len(self.server.received))

    def test_bugsnag_middleware_crash_on_start(self):

        class CrashOnStartApp(object):
            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnStartApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['context'], 'GET /beans')
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_enable_environment(self):
        bugsnag.configure(send_environment=True)

        class CrashOnStartApp(object):
            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnStartApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['environment']['PATH_INFO'],
                         '/beans')

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_middleware_crash_on_iter(self):
        class CrashOnIterApp:
            def __init__(self, environ, start_response):
                pass

            def __iter__(self):
                return self

            def __next__(self):
                raise SentinelError("oops")
        app = TestApp(BugsnagMiddleware(CrashOnIterApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_middleware_crash_on_close(self):
        class CrashOnCloseApp:
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

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_middleware_respects_user_id(self):

        class CrashAfterSettingUserId(object):
            def __init__(self, environ, start_response):
                bugsnag.configure_request(user={
                    "id": "5",
                    "email": "me@cirw.in",
                    "name": "conrad",
                })
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashAfterSettingUserId))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        self.assertEqual(payload['events'][0]['user']['id'], '5')

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_middleware_respects_metadata(self):

        class CrashAfterSettingMetaData(object):
            def __init__(self, environ, start_response):
                bugsnag.configure_request(metadata={"account":
                                                    {"paying": True}})

            def __iter__(self):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashAfterSettingMetaData))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['account'], {"paying": True})

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

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

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_middleware_attaches_unhandled_data(self):

        class CrashOnStartApp(object):

            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnStartApp))

        self.assertRaises(SentinelError, lambda: app.get('/beans'))

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]

        self.assertTrue(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            'type': 'unhandledExceptionMiddleware',
            'attributes': {
                'framework': 'WSGI'
            }
        })

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_read_request_in_callback(self):

        class MyApp(object):

            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        def callback(event):
            event.set_user(id=event.request.GET['user_id'])

        bugsnag.before_notify(callback)
        app = TestApp(BugsnagMiddleware(MyApp))

        with pytest.raises(SentinelError):
            app.get('/beans?user_id=my_id')

        assert len(self.server.received) == 1
        payload = self.server.received[0]['json_body']
        assert payload['events'][0]['user']['id'] == 'my_id'

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/beans'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_middleware_leaves_breadcrumb_with_referer(self):
        class CrashOnStartApp(object):
            def __init__(self, environ, start_response):
                raise SentinelError("oops")

        app = TestApp(BugsnagMiddleware(CrashOnStartApp))
        headers = {'referer': 'http://localhost/toast?password=hunter2'}

        self.assertRaises(
            SentinelError,
            lambda: app.get('/beans', headers=headers)
        )

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['context'], 'GET /beans')
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {
            'to': '/beans',
            'from': 'http://localhost/toast'
        }
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value
