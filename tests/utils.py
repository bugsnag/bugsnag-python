import json
import unittest
from threading import Thread

from six.moves import BaseHTTPServer

import bugsnag


class IntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = FakeBugsnagServer()

    def setUp(self):
        self.server.received = []

    def tearDown(self):
        bugsnag.configuration = bugsnag.Configuration()
        bugsnag.configuration.api_key = 'some key'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()


class FakeBugsnagServer(object):
    """
    A server which accepts a single request, recording the JSON payload and
    other request information
    """
    host = 'localhost'

    def __init__(self, port=5555):
        self.received = []
        self.port = port

        class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

            def do_POST(handler):
                handler.send_response(200)
                length = int(handler.headers['Content-Length'])
                raw_body = handler.rfile.read(length).decode('utf-8')
                self.received.append({'headers': handler.headers,
                                      'json_body': json.loads(raw_body),
                                      'path': handler.path,
                                      'method': handler.command})

            def log_request(self, *args):
                pass

        self.server = BaseHTTPServer.HTTPServer((self.host, self.port),
                                                Handler)
        self.server.timeout = 0.5
        self.thread = Thread(target=self.server.serve_forever, args=(0.1,))
        self.thread.daemon = True
        self.thread.start()

    @property
    def address(self):
        return '%s:%d' % (self.host, self.port)

    @property
    def url(self):
        return 'http://%s' % self.address

    def shutdown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()


class ScaryException(Exception):
    pass
