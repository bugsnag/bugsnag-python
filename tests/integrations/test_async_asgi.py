import pytest
import bugsnag
from bugsnag.asgi import BugsnagMiddleware


class CustomException(Exception):
    pass


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_normal_http_operation(async_bugsnag_server, asgi_wrapper):
    async def app(scope, recv, send):
        await send({
            'type': 'http.request',
            'body': b'hi hi hi',
        })

    app = asgi_wrapper(BugsnagMiddleware(app))
    resp = await app.request('/')
    assert resp is not None
    assert b'hi hi hi' == resp['body']
    assert len(async_bugsnag_server.events_received) == 0


async def test_routing_crash(async_bugsnag_server, asgi_wrapper):
    async def other_func():
        raise CustomException('fell winds!')

    async def app(scope, recv, send):
        await other_func()
        await send({
            'type': 'http.request',
            'body': b'pineapple',
        })

    app = asgi_wrapper(BugsnagMiddleware(app))

    try:
        await app.request('/')
        assert 0, 'An exception should have been raised'
    except CustomException:
        pass

    payload = await async_bugsnag_server.last_event_request()

    request = payload['events'][0]['metaData']['request']
    assert '/' == request['path']
    assert 'GET' == request['httpMethod']
    assert 'http' == request['type']
    assert 'http://testserver/' == request['url']

    exception = payload['events'][0]['exceptions'][0]
    assert 'test_async_asgi.CustomException' == exception['errorClass']
    assert 'fell winds!' == exception['message']
    assert 'other_func' == exception['stacktrace'][0]['method']
    assert 'app' == exception['stacktrace'][1]['method']


async def test_boot_crash(async_bugsnag_server, asgi_wrapper):
    async def app(scope, recv, send):
        raise CustomException('forgot the map')

    app = asgi_wrapper(BugsnagMiddleware(app))

    try:
        await app.request('/')
        assert 0, 'An exception should have been raised'
    except CustomException:
        pass

    payload = await async_bugsnag_server.last_event_request()
    request = payload['events'][0]['metaData']['request']
    assert '/' == request['path']
    assert 'GET' == request['httpMethod']
    assert 'http' == request['type']
    assert 'http://testserver/' == request['url']
    assert 'testclient' == request['clientIp']
    assert 'testclient' == request['headers']['user-agent']

    exception = payload['events'][0]['exceptions'][0]
    assert 'test_async_asgi.CustomException' == exception['errorClass']
    assert 'forgot the map' == exception['message']


async def test_custom_metadata(async_bugsnag_server, asgi_wrapper):
    async def next_func():
        bugsnag.configure_request(meta_data={'wave': {'size': '35b'}})
        raise CustomException('fell winds!')

    async def app(scope, recv, send):
        await next_func()
        await send({})

    app = asgi_wrapper(BugsnagMiddleware(app))

    try:
        await app.request('/')
        assert 0, 'An exception should have been raised'
    except CustomException:
        pass

    payload = await async_bugsnag_server.last_event_request()
    metadata = payload['events'][0]['metaData']
    request = metadata['request']
    assert '/' == request['path']
    assert 'GET' == request['httpMethod']
    assert 'http' == request['type']
    assert 'http://testserver/' == request['url']
    assert '35b' == metadata['wave']['size']

    exception = payload['events'][0]['exceptions'][0]
    assert 'test_async_asgi.CustomException' == exception['errorClass']
    assert 'fell winds!' == exception['message']
    assert 'next_func' == exception['stacktrace'][0]['method']
    assert 'app' == exception['stacktrace'][1]['method']


async def test_websocket_crash(async_bugsnag_server, asgi_wrapper):
    async def app(scope, receive, send):
        await send({'type': 'websocket.accept'})
        raise CustomException('invalid inputs')
        await send({'type': 'websocket.close'})

    app = asgi_wrapper(BugsnagMiddleware(app))

    try:
        await app.websocket_request('/')
        assert 0, 'An exception should have been raised'
    except CustomException:
        pass

    payload = await async_bugsnag_server.last_event_request()
    metadata = payload['events'][0]['metaData']
    request = metadata['request']
    assert '/' == request['path']
    assert 'httpMethod' not in request
    assert 'websocket' == request['type']
    assert 'ws://testserver/' == request['url']
    assert '13' == request['headers']['sec-websocket-version']

    exception = payload['events'][0]['exceptions'][0]
    assert 'test_async_asgi.CustomException' == exception['errorClass']
    assert 'invalid inputs' == exception['message']
    assert 'app' == exception['stacktrace'][0]['method']


async def test_url_components(async_bugsnag_server, asgi_wrapper):
    async def app(scope, recv, send):
        raise CustomException('forgot the map')

    app = asgi_wrapper(BugsnagMiddleware(app))

    try:
        await app.request('/path', 'page=6')
        assert 0, 'An exception should have been raised'
    except CustomException:
        pass

    payload = await async_bugsnag_server.last_event_request()
    request = payload['events'][0]['metaData']['request']
    assert 'http://testserver/path?page=6' == request['url']
