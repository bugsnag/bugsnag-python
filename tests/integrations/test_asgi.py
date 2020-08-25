from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

import bugsnag
from bugsnag.asgi import BugsnagMiddleware
from tests.utils import IntegrationTest, ScaryException


class TestASGIMiddleware(IntegrationTest):
    def setUp(self):
        super(TestASGIMiddleware, self).setUp()
        bugsnag.configure(endpoint=self.server.url,
                          asynchronous=False,
                          api_key='3874876376238728937')

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

    def test_custom_metadata(self):
        app = Starlette()

        async def next_func():
            bugsnag.configure_request(meta_data={'wave': {'size': '35b'}})
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

    def test_url_components(self):
        app = Starlette()

        @app.route('/path')
        async def index(req):
            raise ScaryException('forgot the map')

        app = TestClient(BugsnagMiddleware(app))

        self.assertRaises(ScaryException, lambda: app.get('/path?page=6#top'))
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        request = payload['events'][0]['metaData']['request']
        self.assertEqual('http://testserver/path?page=6', request['url'])
