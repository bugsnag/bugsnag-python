import sys

from nose.plugins.skip import SkipTest

from bugsnag import Configuration
from bugsnag.delivery import (UrllibDelivery, RequestsDelivery,
                              create_default_delivery)

from tests.utils import IntegrationTest


class DeliveryTest(IntegrationTest):

    def setUp(self):
        super(DeliveryTest, self).setUp()
        self.config = Configuration()
        self.config.configure(api_key='abc',
                              endpoint=self.server.address,
                              use_ssl=False,
                              asynchronous=False)

    def test_urllib_delivery_full_url(self):
        self.config.configure(endpoint=self.server.url, use_ssl=None)
        UrllibDelivery().deliver(self.config, '{"legit": 4}')

        self.assertSentReportCount(1)
        request = self.server.received[0]
        self.assertEqual(request['json_body'], {"legit": 4})

    def test_urllib_delivery(self):
        UrllibDelivery().deliver(self.config, '{"legit": 4}')

        self.assertSentReportCount(1)
        request = self.server.received[0]
        self.assertEqual(request['json_body'], {"legit": 4})
        self.assertEqual(request['headers']['Content-Type'],
                         'application/json')

    def test_requests_delivery(self):
        if sys.version_info < (2, 7):
            raise SkipTest("Requests is incompatible with 2.6")

        try:
            import requests  # noqa
        except ImportError:
            raise SkipTest("Requests is not installed")

        RequestsDelivery().deliver(self.config, '{"legit": 4}')

        self.assertSentReportCount(1)
        request = self.server.received[0]
        self.assertEqual(request['json_body'], {"legit": 4})
        self.assertEqual(request['headers']['Content-Type'],
                         'application/json')

    def test_requests_delivery_full_url(self):
        if sys.version_info < (2, 7):
            raise SkipTest("Requests is incompatible with 2.6")

        try:
            import requests  # noqa
        except ImportError:
            raise SkipTest("Requests is not installed")

        self.config.configure(endpoint=self.server.url)
        del self.config.use_ssl
        RequestsDelivery().deliver(self.config, '{"legit": 4}')

        self.assertSentReportCount(1)
        request = self.server.received[0]
        self.assertEqual(request['json_body'], {'legit': 4})

    def test_create_default_delivery(self):
        delivery = create_default_delivery()

        if 'requests' in sys.modules:
            self.assertTrue(isinstance(delivery, RequestsDelivery))
        else:
            self.assertTrue(isinstance(delivery, UrllibDelivery))
