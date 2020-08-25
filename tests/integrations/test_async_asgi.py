import bugsnag
from bugsnag.asgi import BugsnagMiddleware
from tests.async_utils import AsyncIntegrationTest, ASGITestClient


class CustomException(Exception):
    pass


class TestASGIMiddleware(AsyncIntegrationTest):
    async def test_normal_http_operation(self):
        async def app(scope, recv, send):
            await send({
                'type': 'http.request',
                'body': b'hi hi hi',
            })

        app = ASGITestClient(BugsnagMiddleware(app))
        resp = await app.request('/')
        assert resp is not None
        assert b'hi hi hi' == resp['body']
        assert len(self.server.events_received) == 0

    async def test_routing_crash(self):
        async def other_func():
            raise CustomException('fell winds!')

        async def app(scope, recv, send):
            await other_func()
            await send({
                'type': 'http.request',
                'body': b'pineapple',
            })

        app = ASGITestClient(BugsnagMiddleware(app))

        try:
            await app.request('/')
            assert 0, 'An exception should have been raised'
        except CustomException:
            pass

        payload = await self.last_event_request()

        request = payload['events'][0]['metaData']['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('test_async_asgi.CustomException',
                         exception['errorClass'])
        self.assertEqual('fell winds!', exception['message'])
        self.assertEqual('other_func', exception['stacktrace'][0]['method'])
        self.assertEqual('app', exception['stacktrace'][1]['method'])

    async def test_boot_crash(self):
        async def app(scope, recv, send):
            raise CustomException('forgot the map')

        app = ASGITestClient(BugsnagMiddleware(app))

        try:
            await app.request('/')
            assert 0, 'An exception should have been raised'
        except CustomException:
            pass

        payload = await self.last_event_request()
        request = payload['events'][0]['metaData']['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])
        self.assertEqual('testclient', request['clientIp'])
        self.assertEqual('testclient', request['headers']['user-agent'])
        assert 'environment' not in payload['events'][0]['metaData']

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('test_async_asgi.CustomException',
                         exception['errorClass'])
        self.assertEqual('forgot the map', exception['message'])

    async def test_enable_environment(self):
        bugsnag.configure(send_environment=True)

        async def app(scope, recv, send):
            raise CustomException('forgot the map')

        app = ASGITestClient(BugsnagMiddleware(app))

        try:
            await app.request('/')
            assert 0, 'An exception should have been raised'
        except CustomException:
            pass

        payload = await self.last_event_request()
        metadata = payload['events'][0]['metaData']
        self.assertEqual('/', metadata['environment']['path'])

    async def test_custom_metadata(self):
        async def next_func():
            bugsnag.configure_request(meta_data={'wave': {'size': '35b'}})
            raise CustomException('fell winds!')

        async def app(scope, recv, send):
            await next_func()
            await send({})

        app = ASGITestClient(BugsnagMiddleware(app))

        try:
            await app.request('/')
            assert 0, 'An exception should have been raised'
        except CustomException:
            pass

        payload = await self.last_event_request()
        metadata = payload['events'][0]['metaData']
        request = metadata['request']
        self.assertEqual('/', request['path'])
        self.assertEqual('GET', request['httpMethod'])
        self.assertEqual('http', request['type'])
        self.assertEqual('http://testserver/', request['url'])
        self.assertEqual('35b', metadata['wave']['size'])

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('test_async_asgi.CustomException',
                         exception['errorClass'])
        self.assertEqual('fell winds!', exception['message'])
        self.assertEqual('next_func', exception['stacktrace'][0]['method'])
        self.assertEqual('app', exception['stacktrace'][1]['method'])

    async def test_websocket_crash(self):
        async def app(scope, receive, send):
            await send({'type': 'websocket.accept'})
            raise CustomException('invalid inputs')
            await send({'type': 'websocket.close'})

        app = ASGITestClient(BugsnagMiddleware(app))

        try:
            await app.websocket_request('/')
            assert 0, 'An exception should have been raised'
        except CustomException:
            pass

        payload = await self.last_event_request()
        metadata = payload['events'][0]['metaData']
        request = metadata['request']
        self.assertEqual('/', request['path'])
        self.assertNotIn('httpMethod', request)
        self.assertEqual('websocket', request['type'])
        self.assertEqual('ws://testserver/', request['url'])
        self.assertEqual('13', request['headers']['sec-websocket-version'])

        exception = payload['events'][0]['exceptions'][0]
        self.assertEqual('test_async_asgi.CustomException',
                         exception['errorClass'])
        self.assertEqual('invalid inputs', exception['message'])
        self.assertEqual('app', exception['stacktrace'][0]['method'])

    async def test_url_components(self):
        async def app(scope, recv, send):
            raise CustomException('forgot the map')

        app = ASGITestClient(BugsnagMiddleware(app))

        try:
            await app.request('/path', 'page=6')
            assert 0, 'An exception should have been raised'
        except CustomException:
            pass

        payload = await self.last_event_request()
        request = payload['events'][0]['metaData']['request']
        self.assertEqual('http://testserver/path?page=6', request['url'])
