from flask import Flask
import json

from bugsnag.flask import handle_exceptions
import bugsnag.notification
from tests.utils import IntegrationTest


class SentinelError(RuntimeError):
    pass


class TestFlask(IntegrationTest):

    def setUp(self):
        super(TestFlask, self).setUp()
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.address,
                          api_key='3874876376238728937',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          asynchronous=False)

    def test_bugsnag_notify(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            bugsnag.notify(SentinelError("oops"))
            return "OK"

        handle_exceptions(app)
        app.test_client().get('/hello')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']

        print(payload)

        self.assertEqual(payload['events'][0]['metaData']['request']['url'],
                         'http://localhost/hello')
