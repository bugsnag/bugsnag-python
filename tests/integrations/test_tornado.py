import bugsnag
import json
from bugsnag.breadcrumbs import BreadcrumbType
from tests.utils import IntegrationTest
from tornado.testing import AsyncHTTPTestCase
from tests.fixtures.tornado import server


class TornadoTests(AsyncHTTPTestCase, IntegrationTest):
    def get_app(self):
        return server.make_app()

    def setUp(self):
        super(TornadoTests, self).setUp()
        bugsnag.configure(
            endpoint=self.server.url,
            session_endpoint=self.server.url,
            api_key='3874876376238728937',
            notify_release_stages=['dev'],
            release_stage='dev',
            asynchronous=False,
            max_breadcrumbs=25,
            auto_capture_sessions=False,
        )

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

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/notify'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_notify_get(self):
        response = self.fetch('/notify?password=asdf', method="GET")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        p = self.get_http_port()
        expectedUrl = \
            'http://127.0.0.1:{}/notify?password=[FILTERED]'.format(p)

        self.assertEqual(event['metaData']['request'], {
            'method': 'GET',
            'url': expectedUrl,
            'path': '/notify',
            'POST': {},
            'GET': {'password': '[FILTERED]'}
        })

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/notify'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

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

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/notify'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

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

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/notify'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

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

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/notify'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_unhandled(self):
        response = self.fetch('/crash', method="GET")
        self.assertEqual(response.code, 500)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        expectedUrl = 'http://127.0.0.1:{}/crash'.format(self.get_http_port())
        self.assertEqual(event['metaData']['request'], {
            'method': 'GET',
            'url': expectedUrl,
            'arguments': {},
            'path': '/crash',
            'POST': {},
            'GET': {}
        })
        assert 'environment' not in payload['events'][0]['metaData']

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/crash'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

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

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/crash'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

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

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/crash'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_ignored_http_error(self):
        response = self.fetch('/unknown_endpoint')
        self.assertEqual(response.code, 404)
        self.assertEqual(len(self.server.received), 0)

    def test_enable_environment(self):
        bugsnag.configure(send_environment=True)
        response = self.fetch('/notify', method="POST", body="test=post")
        self.assertEqual(response.code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['environment']['REQUEST_METHOD'],
                         'POST')

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/notify'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_read_request_in_callback(self):
        self.fetch('/crash_with_callback?user_id=foo')
        assert len(self.server.received) == 1

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        assert event['user']['id'] == 'foo'

        breadcrumbs = event['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/crash_with_callback'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_bugsnag_request_handler_leaves_breadcrumb_with_referer(self):
        referer = 'http://127.0.0.1:{}/abc/xyz?password=hunter2'.format(
            self.get_http_port()
        )

        self.fetch('/crash', headers={'Referer': referer})
        assert len(self.server.received) == 1

        payload = self.server.received[0]['json_body']
        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {
            'to': '/crash',
            'from': 'http://127.0.0.1:{}/abc/xyz'.format(self.get_http_port())
        }
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value
