import asyncio
import json
from typing import Dict, Any
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest import IsolatedAsyncioTestCase

import bugsnag


class AsyncIntegrationTest(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = FakeBugsnag()
        self.sent_report_count = 0
        bugsnag.configure(
            asynchronous=True,
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            api_key='ffffffffffffffffff'
        )

    async def asyncTearDown(self):
        bugsnag.legacy.default_client.uninstall_sys_hook()
        self.server.shutdown()

    async def last_event_request(self):
        """
        Waits for a request to be received by the event server, timing out
        after a few seconds
        """
        async def poll():
            while len(self.server.events_received) == 0:
                await asyncio.sleep(0.1)

            self.sent_report_count += 1
            return self.server.events_received.pop()

        try:
            return await asyncio.wait_for(poll(), timeout=1.0)
        except asyncio.TimeoutError:
            assert 0, 'Timeout while waiting for a request'


class ASGITestClient:
    def __init__(self, app):
        self.app = app

    async def invoke(self, scope):
        received = None

        async def send(message: Dict[str, Any]):
            nonlocal received
            received = message

        async def receive():
            pass

        await self.app(scope, receive, send)
        return received

    async def request(self, path: str, query: str = '', **kwargs):
        return await self.invoke({
            'method': 'GET',
            'path': path,
            'query_string': query.encode(),
            'scheme': 'http',
            'type': 'http',
            'server': ['testserver', 80],
            'client': ['testclient', 8080],
            'headers': [
                [b'user-agent', b'testclient'],
            ],
            **kwargs
        })

    async def websocket_request(self, path: str):
        return await self.invoke({
            'path': path,
            'scheme': 'ws',
            'type': 'websocket',
            'server': ['testserver', 80],
            'client': ['testclient', 8080],
            'headers': [
                [b'user-agent', b'testclient'],
                [b'sec-websocket-version', b'13'],
            ],
        })


class FakeBugsnag:
    def __init__(self):
        self.events_received = []
        self.sessions_received = []
        server = self

        class Handler(SimpleHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers['Content-Length'])
                raw_body = self.rfile.read(length).decode('utf-8')
                json_body = json.loads(raw_body)
                if self.path == '/sessions':
                    server.sessions_received.append(json_body)
                    self.send_response(202)
                elif self.path == '/events':
                    server.events_received.append(json_body)
                    self.send_response(202)
                else:
                    assert 0, ('unknown endpoint requested: {}' % self.path)
                self.end_headers()
                return ()

            def log_request(self, *args):
                pass

        self.server = HTTPServer(('localhost', 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, args=(0.1,))
        self.thread.daemon = True
        self.thread.start()

    @property
    def address(self):
        return '{0}:{1}'.format(*self.server.server_address)

    @property
    def events_url(self):
        return 'http://%s/events' % self.address

    @property
    def sessions_url(self):
        return 'http://%s/sessions' % self.address

    def shutdown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
