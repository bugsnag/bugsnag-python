import sys
import json
import time
import unittest
from threading import Thread

from http.server import SimpleHTTPRequestHandler, HTTPServer

import bugsnag


try:
    import exceptiongroup # noqa
    is_exception_group_supported = True
except ImportError:
    is_exception_group_supported = sys.version_info >= (3, 11)


class MissingRequestError(Exception):
    pass


class IntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = FakeBugsnagServer(wait_for_duplicate_requests=False)

    def setUp(self):
        self.server.events_received = []
        self.server.sessions_received = []

    def tearDown(self):
        previous_client = bugsnag.legacy.default_client
        previous_client.uninstall_sys_hook()

        if previous_client.session_tracker.delivery_thread is not None:
            previous_client.session_tracker.delivery_thread.cancel()
            previous_client.session_tracker.delivery_thread = None

        previous_client.session_tracker.session_counts = {}

        client = bugsnag.Client(api_key='some key')

        bugsnag.legacy.default_client = client
        bugsnag.legacy.configuration = client.configuration

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def assertSentReportCount(self, count):
        self.assertEqual(len(self.server.events_received), count)

    def assertExceptionName(self, received_index, event_index, name):
        json_body = self.server.events_received[received_index]['json_body']
        event = json_body['events'][event_index]
        exception = event['exceptions'][0]
        self.assertEqual(exception['errorClass'], name)

    @property
    def sent_report_count(self) -> int:
        return self.server.sent_report_count

    @property
    def sent_session_count(self) -> int:
        return self.server.sent_session_count


class FakeBugsnagServer(object):
    """
    A server which accepts a single request, recording the JSON payload and
    other request information
    """

    def __init__(self, wait_for_duplicate_requests: bool):
        self.events_received = []
        self.sessions_received = []
        self.paused = False
        self.wait_for_duplicate_requests = wait_for_duplicate_requests

        class Handler(SimpleHTTPRequestHandler):
            def do_POST(handler):
                start = time.time()

                while self.paused:
                    if time.time() > (start + 0.5):
                        raise Exception('Paused HTTP server timeout')

                    time.sleep(0.001)

                length = int(handler.headers['Content-Length'])
                raw_body = handler.rfile.read(length).decode('utf-8')

                if handler.path in ('/sessions', self.sessions_url):
                    self.sessions_received.append({
                        'headers': handler.headers,
                        'json_body': json.loads(raw_body),
                    })
                elif handler.path in ('/events', self.events_url):
                    self.events_received.append({
                        'headers': handler.headers,
                        'json_body': json.loads(raw_body),
                        'method': handler.command,
                        'path': handler.path,
                    })
                elif handler.path == '/ignore':
                    pass
                else:
                    raise Exception(
                        'unknown endpoint requested: ' + handler.path
                    )

                handler.send_response(200)
                handler.end_headers()

                return ()

            def log_request(self, *args):
                pass

        self.server = HTTPServer(('localhost', 0), Handler)
        self.server.timeout = 0.5
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
        self.events_received = []
        self.sessions_received = []

    def wait_for_session(self, timeout=2):
        self._wait_for_request(self.sessions_received, timeout=timeout)

    def wait_for_event(self, timeout=2):
        self._wait_for_request(self.events_received, timeout=timeout)

    def _wait_for_request(self, request_list, timeout):
        start = time.time()

        while len(request_list) == 0:
            if time.time() - start > timeout:
                raise MissingRequestError("No request received before timeout")

            time.sleep(0.01)

        # sleep for the time remaining until 'timeout' to allow more requests
        # to arrive
        if self.wait_for_duplicate_requests:
            time.sleep(timeout - (time.time() - start))

    @property
    def sent_report_count(self) -> int:
        return len(self.events_received)

    @property
    def sent_session_count(self) -> int:
        return len(self.sessions_received)


class ScaryException(Exception):
    class NestedScaryException(Exception):
        pass
