import bugsnag
import json
from tests.utils import IntegrationTest
from tornado.testing import AsyncHTTPTestCase
import tests.fixtures.tornado.server


class TornadoTests(AsyncHTTPTestCase, IntegrationTest):
    def get_app(self):
        return tests.fixtures.tornado.server.make_app()

    def setUp(self):
        super(TornadoTests, self).setUp()
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.address,
                          api_key='3874876376238728937',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          asynchronous=False)

    def test_notify(self):
        response = self.fetch('/notify', method="GET")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        # self.assertEqual(event['metaData']['request'], {
        #     'method': 'GET',
        #     'url': 'http://testserver/notify',
        #     'path': '/notify',
        #     'POST': {},
        #     'GET': {}
        # })
        # SN: The server port changes on each run, hence breaking
        # out the asserts
        self.assertEqual(event['metaData']['request']["method"], "GET")
        self.assertEqual(event['metaData']['request']["path"], "/notify")
        self.assertEqual(event['metaData']['request']["POST"], {})
        self.assertEqual(event['metaData']['request']["GET"], {})

    def test_notify_post(self):
        response = self.fetch('/notify', method="POST", body="test=post")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['request']["method"], "POST")
        self.assertEqual(event['metaData']['request']["path"], "/notify")
        self.assertEqual(event['metaData']['request']["POST"],
                         {'test': ['post']})
        self.assertEqual(event['metaData']['request']["GET"], {})

    def test_notify_json_post(self):
        body = json.dumps({'test': 'json_post'})
        response = self.fetch('/notify', method="POST", body=body,
                              headers={'Content-Type': 'application/json'})
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        print(event['metaData']['request'])
        self.assertEqual(event['metaData']['request']["method"], "POST")
        self.assertEqual(event['metaData']['request']["path"], "/notify")
        self.assertEqual(event['metaData']['request']["POST"],
                         {'test': 'json_post'})
        self.assertEqual(event['metaData']['request']["GET"], {})
