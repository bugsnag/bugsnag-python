from enum import Enum
from typing import Any, List, Dict, Union, Optional

import bugsnag
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.legacy import _auto_leave_breadcrumb
from bugsnag.utils import sanitize_url

__all__ = ('BugsnagMiddleware',)

SEVERITY_REASON = {
    "type": "unhandledExceptionMiddleware",
    "attributes": {
        "framework": "ASGI"
    }
}

DEFAULT_PORTS = {"http": 80, "https": 443, "ws": 80, "wss": 443}


def parse_host_header(headers: Dict[bytes, bytes]) -> Union[None, str]:
    if b'host' in headers:
        return headers[b'host'].decode('latin-1', 'ignore')
    return None


def parse_server_host(scheme: str, server) -> Union[None, str]:
    if len(server) == 2:
        hostname, port = server
        if port == DEFAULT_PORTS[scheme]:
            return hostname
        else:
            return '{}:{}'.format(hostname, port)
    return None


def parse_url(request: dict, server: List[Any]) -> str:
    scheme = request.get('scheme', 'http')
    query = request.get('query', None)
    path = request.get('path', '/')
    headers = request.get('headers', dict())
    host = parse_host_header(headers) or parse_server_host(scheme, server)
    url = ''
    if host is not None:
        url += '{}://{}'.format(scheme, host)
    url += path
    if query is not None and len(query) > 0:
        url += '?{}'.format(query.decode('utf-8', 'ignore'))

    return url


class RequestMetadata(Enum):
    http_method = ('httpMethod', ['method', 'http_method'])
    http_version = ('httpVersion', ['http_version'])
    path = ('path', ['path'])
    scheme = ('scheme', ['scheme'])
    type = ('type', ['type'])
    query = ('query', ['query_string'])

    def __init__(self, metadata_key: str, scope_keys: List[str]):
        self.metadata_key = metadata_key
        self.scope_keys = scope_keys


class BugsnagMiddleware:
    """
    Sends unhandled exceptions to Bugsnag which happen while processing
    requests.

    >>> async def app(scope, receive, send):
    ...     await send({
    ...         "type": "http.request",
    ...         "body": b"Hello World",
    ...         "more_body": False,
    ...     })
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
            server = []

            client = scope.get('client')
            if client is not None and len(client) > 0:
                request['clientIp'] = scope['client'][0]

            if 'server' in scope and type(scope['server']) in [list, tuple]:
                server = scope['server']
            if 'headers' in scope:
                request['headers'] = dict(
                        [i for i in scope['headers'] if len(i) == 2])
            for prop in RequestMetadata:
                for item in prop.scope_keys:
                    if item in scope:
                        request[prop.metadata_key] = scope[item]
                        break

            request['url'] = parse_url(request, server)

            event.add_tab("request", request)
            if bugsnag.configure().send_environment:
                event.add_tab("environment", scope)

        stack.before_notify(add_request_info)

    async def __call__(self, scope, receive, send):
        bugsnag.configure()._breadcrumbs.create_copy_for_context()
        bugsnag.configure_request(asgi_scope=scope)
        try:
            if bugsnag.configuration.auto_capture_sessions:
                bugsnag.start_session()

            # only HTTP and Websocket requests have headers
            if scope['type'] in ('http', 'websocket'):
                _auto_leave_breadcrumb(
                    '{} request'.format(scope['type']),
                    _get_breadcrumb_metadata(scope),
                    BreadcrumbType.NAVIGATION
                )

            await self.app(scope, receive, send)
        except Exception as e:
            bugsnag.auto_notify(e, severity_reason=SEVERITY_REASON)
            raise


def _get_breadcrumb_metadata(scope) -> Dict[str, str]:
    metadata = {'to': scope['path']}
    referer = _get_referer_header(scope)

    if referer:
        metadata['from'] = sanitize_url(referer)

    return metadata


def _get_referer_header(scope) -> Optional[str]:
    for key, value in scope['headers']:
        if key == b'referer':
            return value.decode('latin-1', 'ignore')

    return None
