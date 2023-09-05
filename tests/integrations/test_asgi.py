from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

import bugsnag
from bugsnag.asgi import BugsnagMiddleware
from bugsnag.breadcrumbs import BreadcrumbType
from tests.utils import IntegrationTest, ScaryException

import pytest


class TestASGIMiddleware(IntegrationTest):
    def setUp(self):
        super(TestASGIMiddleware, self).setUp()
        bugsnag.configure(endpoint=self.server.url,
                          asynchronous=False,
                          api_key='3874876376238728937',
                          max_breadcrumbs=25)

    def test_normal_http_operation(self):
        async def app(scope, recv, send):
            response = PlainTextResponse('hi hi hi')
            await response(scope, recv, send)

        app = TestClient(BugsnagMiddleware(app))
        resp = app.get('/')

        self.assertEqual('hi hi hi', resp.text)
        self.assertSentReportCount(0)

    def test_routing_crash(self):
        app = Starlette()

        async def other_func():
            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            await other_func()
            return PlainTextResponse('pineapple')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(ScaryException, lambda: app.get('/'))
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        request = payload['events'][0]['metaData']['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])
        assert 'environment' not in payload['events'][0]['metaData']

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])
        self.assertEqual('fell winds!', exception['message'])
        self.assertEqual('other_func', exception['stacktrace'][0]['method'])
        self.assertEqual('index', exception['stacktrace'][1]['method'])

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_enable_environment(self):
        bugsnag.configure(send_environment=True)
        app = Starlette()

        async def other_func():
            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            await other_func()
            return PlainTextResponse('pineapple')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(ScaryException, lambda: app.get('/'))
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        environment = payload['events'][0]['metaData']['environment']

        self.assertEqual('/', environment['path'])

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_headers_are_filtered(self):
        bugsnag.configure()
        app = Starlette()

        async def other_func():
            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            await other_func()
            return PlainTextResponse('pineapple')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(
            ScaryException,
            lambda: app.get('/', headers={'Authorization': 'yes'})
        )
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        headers = payload['events'][0]['metaData']['request']['headers']

        self.assertEqual('[FILTERED]', headers['authorization'])

    def test_boot_crash(self):
        async def app(scope, recv, send):
            raise ScaryException('forgot the map')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(ScaryException, lambda: app.get('/'))
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        request = payload['events'][0]['metaData']['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])
        self.assertEqual('testclient', request['clientIp'])
        self.assertEqual('testclient', request['headers']['user-agent'])

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])
        self.assertEqual('forgot the map', exception['message'])

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_custom_metadata(self):
        app = Starlette()

        async def next_func():
            bugsnag.configure_request(metadata={'wave': {'size': '35b'}})
            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            await next_func()
            return PlainTextResponse('pineapple')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(ScaryException, lambda: app.get('/'))
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        metadata = payload['events'][0]['metaData']
        request = metadata['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])
        self.assertEqual('35b', metadata['wave']['size'])

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])
        self.assertEqual('fell winds!', exception['message'])
        self.assertEqual('next_func', exception['stacktrace'][0]['method'])
        self.assertEqual('index', exception['stacktrace'][1]['method'])

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_websocket_crash(self):
        async def app(scope, receive, send):
            websocket = WebSocket(scope, receive=receive, send=send)
            await websocket.accept()
            raise ScaryException('invalid inputs')
            await websocket.close()

        app = TestClient(BugsnagMiddleware(app))
        with app.websocket_connect('/') as websocket:
            self.assertRaises(ScaryException, lambda: websocket.receive_text())

        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        metadata = payload['events'][0]['metaData']
        request = metadata['request']
        self.assertEqual('/', request['path'])
        self.assertNotIn('httpMethod', request)
        self.assertEqual('websocket', request['type'])
        self.assertEqual('ws://testserver/', request['url'])
        self.assertEqual('13', request['headers']['sec-websocket-version'])

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])
        self.assertEqual('invalid inputs', exception['message'])
        self.assertEqual('app', exception['stacktrace'][0]['method'])

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'websocket request'
        assert breadcrumbs[0]['metaData'] == {'to': '/'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_url_components(self):
        app = Starlette()

        @app.route('/path')
        async def index(req):
            raise ScaryException('forgot the map')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(
            ScaryException,
            lambda: app.get('/path?password=secret#top')
        )
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        request = payload['events'][0]['metaData']['request']
        self.assertEqual(
            'http://testserver/path?password=[FILTERED]',
            request['url']
        )

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/path'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_breadcrumb_records_the_referer_header(self):
        app = Starlette()

        async def other_func():
            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            await other_func()
            return PlainTextResponse('pineapple')

        app = TestClient(BugsnagMiddleware(app))
        headers = {'referer': 'http://testserver/abc/xyz?password=hunter2'}

        self.assertRaises(
            ScaryException,
            lambda: app.get('/', headers=headers)
        )
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        request = payload['events'][0]['metaData']['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])
        assert 'environment' not in payload['events'][0]['metaData']

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])
        self.assertEqual('fell winds!', exception['message'])
        self.assertEqual('other_func', exception['stacktrace'][0]['method'])
        self.assertEqual('index', exception['stacktrace'][1]['method'])

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {
            'to': '/',
            'from': 'http://testserver/abc/xyz'
        }
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_chained_exceptions(self):
        app = Starlette()

        async def other_func():
            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            try:
                await other_func()
            except ScaryException as scary:
                raise Exception('disconcerting breeze.') from scary

        app = TestClient(BugsnagMiddleware(app))

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 1

        payload = self.server.received[0]['json_body']

        print(payload)
        assert len(payload['events'][0]['exceptions']) == 2

        exception1 = payload['events'][0]['exceptions'][0]
        exception2 = payload['events'][0]['exceptions'][1]

        assert 'Exception' == exception1['errorClass']
        assert 'disconcerting breeze.' == exception1['message']
        assert 'index' == exception1['stacktrace'][0]['method']

        assert 'tests.utils.ScaryException' == exception2['errorClass']
        assert 'fell winds!' == exception2['message']
        assert len(exception2['stacktrace']) == 2
        assert 'other_func' == exception2['stacktrace'][0]['method']
        assert 'index' == exception2['stacktrace'][1]['method']

    def test_feature_flags_dont_leak_between_requests(self):
        count = 0
        app = Starlette()

        async def other_func():
            nonlocal count
            count += 1
            bugsnag.add_feature_flag(str(count), 'b')

            if count > 4:
                bugsnag.clear_feature_flags()

            raise ScaryException('fell winds!')

        @app.route('/')
        async def index(req):
            nonlocal count
            count += 1
            bugsnag.add_feature_flag(str(count), 'a')

            await other_func()
            return PlainTextResponse('pineapple')

        app = TestClient(BugsnagMiddleware(app))

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 1

        payload = self.server.received[0]['json_body']
        exception = payload['events'][0]['exceptions'][0]
        feature_flags = payload['events'][0]['featureFlags']

        assert exception['errorClass'] == 'tests.utils.ScaryException'
        assert exception['message'] == 'fell winds!'
        assert exception['stacktrace'][0]['method'] == 'other_func'
        assert exception['stacktrace'][1]['method'] == 'index'

        assert feature_flags == [
            {'featureFlag': '1', 'variant': 'a'},
            {'featureFlag': '2', 'variant': 'b'}
        ]

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 2

        payload = self.server.received[1]['json_body']
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == [
            {'featureFlag': '3', 'variant': 'a'},
            {'featureFlag': '4', 'variant': 'b'}
        ]

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 3

        payload = self.server.received[2]['json_body']
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == []
