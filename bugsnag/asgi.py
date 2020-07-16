from enum import Enum

import bugsnag

__all__ = ('BugsnagMiddleware',)

SEVERITY_REASON = {
    "type": "unhandledExceptionMiddleware",
    "attributes": {
        "framework": "ASGI"
    }
}


class RequestMetadata(Enum):
    http_method = ('httpMethod', ['method', 'http_method'])
    http_version = ('httpVersion', ['http_version'])
    path = ('path', ['path'])
    type = ('type', ['type'])
    query = ('query', ['query_string'])

    def __init__(self, metadata_key, scope_keys):
        self.metadata_key = metadata_key
        self.scope_keys = scope_keys


class BugsnagMiddleware:
    """
    Sends unhandled exceptions to Bugsnag which happen while processing
    requests.

    >>> async def app(scope, receive, send):
    >>>     await send({
    >>>         "type": "http.request",
    >>>         "body": b"Hello World",
    >>>         "more_body": False,
    >>>     })
    >>> app = BugsnagMiddleware(app)
    """
    def __init__(self, app):
        self.app = app
        stack = bugsnag.configure().internal_middleware

        def add_request_info(event):
            if not hasattr(event.request_config, 'asgi_scope'):
                return

            scope = event.request_config.asgi_scope
            request = dict()
            if 'client' in scope and len(scope['client']) > 0:
                request['clientIp'] = scope['client'][0]
            if 'server' in scope:
                request['url'] = ':'.join([str(it) for it in scope['server']])
            if 'headers' in scope:
                request['headers'] = dict(
                        [i for i in scope['headers'] if len(i) == 2])
            for prop in RequestMetadata:
                for item in prop.scope_keys:
                    if item in scope:
                        request[prop.metadata_key] = scope[item]
                        break

            event.add_tab("request", request)

        stack.before_notify(add_request_info)

    async def __call__(self, scope, receive, send):
        bugsnag.configure_request(asgi_scope=scope)
        try:
            if bugsnag.configuration.auto_capture_sessions:
                bugsnag.start_session()
            await self.app(scope, receive, send)
        except Exception as e:
            bugsnag.auto_notify(e, severity_reason=SEVERITY_REASON)
            raise
