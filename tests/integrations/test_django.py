from django.http import HttpResponse
from django.test import TestCase, RequestFactory, Client, modify_settings

import bugsnag
from bugsnag.django.middleware import BugsnagMiddleware

from tests.utils import FakeBugsnagServer


class TestDjango(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestDjango, cls).setUpClass()
        cls.server = FakeBugsnagServer()

    def setUp(self):
        super(TestDjango, self).setUp()
        self.factory = RequestFactory()
        with self.settings(BUGSNAG={'api_key': 'burgers',
                                    'endpoint': self.server.url}):
            self.middleware = BugsnagMiddleware()
        self.server.received = []

    def tearDown(self):
        super(TestDjango, self).tearDown()
        client = bugsnag.Client()
        client.configuration.api_key = 'some key'
        bugsnag.legacy.default_client = client
        bugsnag.legacy.configuration = client.configuration

    @classmethod
    def tearDownClass(cls):
        super(TestDjango, cls).tearDownClass()
        cls.server.shutdown()

    def test_bugsnag_middleware_installed(self):
        request = self.factory.get('/foo')
        self.middleware.process_request(request)

        self.assertEqual(len(self.server.received), 0)

    def test_bugsnag_middleware_server_error(self):
        request = self.factory.get('/foo')
        self.middleware.process_request(request)
        self.middleware.process_exception(request, RuntimeError(':('))

        self.assertEqual(len(self.server.received), 1)
