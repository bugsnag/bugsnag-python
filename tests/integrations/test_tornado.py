import bugsnag
import json
from tests.utils import IntegrationTest
from tornado.testing import AsyncHTTPTestCase
from tests.fixtures.tornado import server


class TornadoTests(AsyncHTTPTestCase, IntegrationTest):
    def get_app(self):
        return server.make_app()

    def setUp(self):
        super(TornadoTests, self).setUp()
        bugsnag.configure(endpoint=self.server.url,
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
        expectedUrl = 'http://127.0.0.1:{}/notify'.format(self.get_http_port())
        self.assertEqual(event['metaData']['request'], {
            'method': 'GET',
            'url': expectedUrl,
            'path': '/notify',
            'POST': {},
            'GET': {}
        })

    def test_notify_get(self):
        response = self.fetch('/notify?test=get', method="GET")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        p = self.get_http_port()
        expectedUrl = 'http://127.0.0.1:{}/notify?test=get'.format(p)
        self.assertEqual(event['metaData']['request'], {
            'method': 'GET',
            'url': expectedUrl,
            'path': '/notify',
            'POST': {},
            'GET': {'test': ['get']}
        })

    def test_notify_post(self):
        response = self.fetch('/notify', method="POST", body="test=post")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        expectedUrl = 'http://127.0.0.1:{}/notify'.format(self.get_http_port())
        self.assertEqual(event['metaData']['request'], {
            'method': 'POST',
            'url': expectedUrl,
            'path': '/notify',
            'POST': {'test': ['post']},
            'GET': {}
        })

    def test_notify_json_post(self):
        body = json.dumps({'test': 'json_post'})
        response = self.fetch('/notify', method="POST", body=body,
                              headers={'Content-Type': 'application/json'})
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        expectedUrl = 'http://127.0.0.1:{}/notify'.format(self.get_http_port())
        self.assertEqual(event['metaData']['request'], {
            'method': 'POST',
            'url': expectedUrl,
            'path': '/notify',
            'POST': {'test': 'json_post'},
            'GET': {}
        })

    def test_notify_json_subtype_post(self):
        body = {
            '$id': 'https://example.com/person.schema.json',
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'title': 'Dog',
            'type': 'object',
            "properties": {
                'sound': {
                    'type': 'str',
                    'description': 'The sound the dog makes'
                }
            }
        }
        headers = {'Content-Type': 'application/schema+json'}
        response = self.fetch('/notify', method="POST", body=json.dumps(body),
                              headers=headers)
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['request'], {
            'method': 'POST',
            'url': 'http://127.0.0.1:{}/notify'.format(self.get_http_port()),
            'path': '/notify',
            'POST': body,
            'GET': {}
        })

    def test_unhandled(self):
        response = self.fetch('/crash', method="GET")
        self.assertEqual(response.code, 500)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        expectedUrl = 'http://127.0.0.1:{}/crash'.format(self.get_http_port())
        self.assertEqual(event['metaData']['environment'], {})
        self.assertEqual(event['metaData']['request'], {
            'method': 'GET',
            'url': expectedUrl,
            'arguments': {},
            'path': '/crash',
            'POST': {},
            'GET': {}
        })

    def test_unhandled_post(self):
        response = self.fetch('/crash', method="POST", body="test=post")
        self.assertEqual(response.code, 500)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        expectedUrl = 'http://127.0.0.1:{}/crash'.format(self.get_http_port())
        self.assertEqual(event['metaData']['request'], {
            'method': 'POST',
            'url': expectedUrl,
            'arguments': {'test': ['post']},
            'path': '/crash',
            'POST': {'test': ['post']},
            'GET': {}
        })

    def test_unhandled_json_post(self):
        body = json.dumps({'test': 'json_post'})
        response = self.fetch('/crash', method="POST", body=body,
                              headers={'Content-Type': 'application/json'})
        self.assertEqual(response.code, 500)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        expectedUrl = 'http://127.0.0.1:{}/crash'.format(self.get_http_port())
        self.assertEqual(event['metaData']['request'], {
            'method': 'POST',
            'url': expectedUrl,
            'arguments': {},
            'path': '/crash',
            'POST': {'test': 'json_post'},
            'GET': {}
        })

    def test_ignored_http_error(self):
        response = self.fetch('/unknown_endpoint')
        self.assertEqual(response.code, 404)
        self.assertEqual(len(self.server.received), 0)

    def test_disable_environment(self):
        bugsnag.configure(send_environment=False)
        response = self.fetch('/notify', method="POST", body="test=post")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        assert 'environment' not in payload['events'][0]['metaData']
