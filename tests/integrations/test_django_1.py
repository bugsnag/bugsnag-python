import sys
import os
import re
from tests.utils import IntegrationTest

import django
from django.test import Client

EXAMPLE_PATH = os.path.join(__file__, '..', '..', 'fixtures', 'django1')
sys.path.append(os.path.abspath(EXAMPLE_PATH))
os.environ['DJANGO_SETTINGS_MODULE'] = 'bugsnag_demo.settings'


class DjangoMiddlewareTests(IntegrationTest):
    def setUp(self):
        super(DjangoMiddlewareTests, self).setUp()

        os.environ['BUGSNAG_API'] = self.server.url
        django.setup()
        self.client = Client()

        # This isn't nice, but is required as settings setup must happen first
        from django.contrib.auth.models import User
        User.objects.all().delete()
        self.user = User.objects.create_user(
            username='test',
            email='test@test.com',
            password='hunter2'
        )

    def test_notify(self):
        response = self.client.get('/notify/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['request'], {
            'method': 'GET',
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
            'method': 'GET',
            'url': 'http://testserver/crash/',
            'path': '/crash/',
            'POST': {},
            'encoding': None,
            'GET': {}
        })

    def test_ignores_http404(self):
        self.client.get('/404')
        self.assertEqual(len(self.server.received), 0)

    def test_django_intergration_includes_middleware_severity(self):
        with self.assertRaises(Exception):
            self.client.get('/crash/')

        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]

        self.assertTrue(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            'type': 'unhandledExceptionMiddleware',
            'attributes': {
                'framework': 'Django'
            }
        })

    def test_appends_user_data(self):
        self.client.login(username='test', password='hunter2')
        with self.assertRaises(Exception):
            self.client.get('/crash/')

        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        user = payload['events'][0]['user']

        self.assertEqual(user, {
            'id': self.user.username,
            'email': 'test@test.com'
        })

    def test_appends_framework_version(self):
        with self.assertRaises(Exception):
            self.client.get('/crash/')

        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        device_data = payload['events'][0]['device']

        self.assertEquals(len(device_data['runtimeVersions']), 2)
        self.assertTrue(re.match(r'\d+\.\d+\.\d+',
                                 device_data['runtimeVersions']['python']))
        self.assertTrue(re.match(r'\d+\.\d+\.\d+',
                                 device_data['runtimeVersions']['django']))
