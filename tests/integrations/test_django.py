import sys
import os
from tests.utils import IntegrationTest

import django
from django.test import Client

EXAMPLE_PATH = os.path.join(__file__, '..', '..', '..', 'example', 'django')
sys.path.append(os.path.abspath(EXAMPLE_PATH))
os.environ['DJANGO_SETTINGS_MODULE'] = 'bugsnag_demo.settings'


class DjangoMiddlewareTests(IntegrationTest):
    def setUp(self):
        super(DjangoMiddlewareTests, self).setUp()

        os.environ['BUGSNAG_API'] = self.server.url
        django.setup()
        self.client = Client()

    def test_notify(self):
        response = self.client.get('/notify/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['request'], {
            'url': 'http://testserver/notify/',
            'path': '/notify/',
            'POST': {},
            'encoding': None,
            'GET': {}
        })

    def test_unhandled_exception(self):
        with self.assertRaises(Exception):
            self.client.get('/crash/')

        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['request'], {
            'url': 'http://testserver/crash/',
            'path': '/crash/',
            'POST': {},
            'encoding': None,
            'GET': {}
        })

    def test_ignores_http404(self):
        self.client.get('/404')
        self.assertEqual(len(self.server.received), 0)
