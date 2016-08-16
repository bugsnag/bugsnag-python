import json
from threading import Thread

from six.moves import BaseHTTPServer


class FakeBugsnagServer(object):
    """
    A server which accepts a single request, recording the JSON payload and
    other request information
    """
    host = 'localhost'
    json_body = None

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

        self.server = BaseHTTPServer.HTTPServer((self.host, self.port),
                                                Handler)
        self.server.timeout = 0.5
        self.thread = Thread(target=self.server.serve_forever, args=(0.1,))
        self.thread.daemon = True
        self.thread.start()

    def url(self):
        return '%s:%d' % (self.host, self.port)

    def shutdown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()


class ScaryException(Exception):
    pass
