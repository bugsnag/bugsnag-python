import sys

from nose.plugins.skip import SkipTest
if (3, 0) <= sys.version_info < (3, 3):  # noqa
    raise SkipTest("Flask is incompatible with python3 3.0 - 3.2")
import unittest

from flask import Flask

from bugsnag.flask import handle_exceptions
import bugsnag.notification
from tests.utils import FakeBugsnagServer


class SentinelError(RuntimeError):
    pass


class TestFlask(unittest.TestCase):

    def setUp(self):
        self.server = FakeBugsnagServer(5435)
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.url(),
                          api_key='3874876376238728937',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          async=False)

    def shutDown(self):
        bugsnag.configuration = bugsnag.Configuration()
        bugsnag.configuration.api_key = 'some key'

    def test_bugsnag_middleware_working(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            return "OK"

        handle_exceptions(app)

        resp = app.test_client().get('/hello')
        self.assertEqual(resp.data, b'OK')
        self.server.shutdown()

        self.assertEqual(0, len(self.server.received))

    def test_bugsnag_crash(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().get('/hello')
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        self.assertEqual(payload['events'][0]['exceptions'][0]['errorClass'],
                         'tests.test_flask.SentinelError')
        self.assertEqual(payload['events'][0]['metaData']['request']['url'],
                         'http://localhost/hello')

    def test_bugsnag_notify(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            bugsnag.notify(SentinelError("oops"))
            return "OK"

        handle_exceptions(app)
        app.test_client().get('/hello')
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        self.assertEqual(payload['events'][0]['metaData']['request']['url'],
                         'http://localhost/hello')

    def test_bugsnag_custom_data(self):
        meta_data = [{"hello": {"world": "once"}},
                     {"again": {"hello": "world"}}]

        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            bugsnag.configure_request(meta_data=meta_data.pop())
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().get('/hello')
        app.test_client().get('/hello')
        self.server.shutdown()

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData'].get('hello'), None)
        self.assertEqual(event['metaData']['again']['hello'], 'world')

        payload = self.server.received[1]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['hello']['world'], 'once')
        self.assertEqual(event['metaData'].get('again'), None)
        self.assertEqual(2, len(self.server.received))

    def test_bugsnag_includes_posted_json_data(self):
        app = Flask("bugsnag")

        @app.route("/ajax", methods=["POST"])
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().post(
            '/ajax', data='{"key": "value"}', content_type='application/json')
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'tests.test_flask.SentinelError')
        self.assertEqual(event['metaData']['request']['url'],
                         'http://localhost/ajax')
        self.assertEqual(event['metaData']['request']['data'],
                         dict(key='value'))

    def test_bugsnag_add_metadata_tab(self):
        app = Flask("bugsnag")

        @app.route("/form", methods=["PUT"])
        def hello():
            bugsnag.add_metadata_tab("account", {"id": 1, "premium": True})
            bugsnag.add_metadata_tab("account", {"premium": False})
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().put(
            '/form', data='_data', content_type='application/octet-stream')
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['account']['premium'], False)
        self.assertEqual(event['metaData']['account']['id'], 1)

    def test_bugsnag_includes_unknown_content_type_posted_data(self):
        app = Flask("bugsnag")

        @app.route("/form", methods=["PUT"])
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().put(
            '/form', data='_data', content_type='application/octet-stream')
        self.server.shutdown()

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'tests.test_flask.SentinelError')
        self.assertEqual(event['metaData']['request']['url'],
                         'http://localhost/form')
        body = event['metaData']['request']['data']['body']
        self.assertTrue('_data' in body)
