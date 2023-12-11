import warnings
import sys

from bugsnag import Configuration
from bugsnag.delivery import (
    UrllibDelivery,
    RequestsDelivery,
    create_default_delivery,
    DEFAULT_SESSIONS_ENDPOINT
)

from tests.utils import IntegrationTest


class DeliveryTest(IntegrationTest):

    def setUp(self):
        super(DeliveryTest, self).setUp()
        self.config = Configuration()
        self.config.configure(
            api_key='abc',
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            asynchronous=False
        )

    def test_urllib_delivery(self):
        UrllibDelivery().deliver(self.config, '{"legit": 4}')

        self.assertSentReportCount(1)
        request = self.server.events_received[0]
        self.assertEqual(request['json_body'], {"legit": 4})
        self.assertEqual(request['headers']['Content-Type'],
                         'application/json')

    def test_create_default_delivery(self):
        delivery = create_default_delivery()

        if 'requests' in sys.modules:
            self.assertTrue(isinstance(delivery, RequestsDelivery))
        else:
            self.assertTrue(isinstance(delivery, UrllibDelivery))

    def test_misconfigured_sessions_endpoint_sends_warning(self):
        delivery = create_default_delivery()

        self.config.configure(session_endpoint=self.server.sessions_url)

        with warnings.catch_warnings(record=True) as warn:
            warnings.simplefilter("always")
            delivery.deliver_sessions(self.config, '{"apiKey":"aaab"}')
            self.assertEqual(0, len(warn))
            self.assertEqual(1, len(self.server.sessions_received))

        self.server.sessions_received.clear()
        self.config.configure(session_endpoint=DEFAULT_SESSIONS_ENDPOINT)

        with warnings.catch_warnings(record=True) as warn:
            warnings.simplefilter("always")
            delivery.deliver_sessions(self.config, '{"apiKey":"aaab"}')
            self.assertEqual(1, len(warn))
            self.assertEqual(0, len(self.server.sessions_received))
            self.assertTrue('No sessions will be sent' in str(warn[0].message))
            delivery.deliver_sessions(self.config, '{"apiKey":"aaab"}')
            self.assertEqual(1, len(warn))
            self.assertEqual(0, len(self.server.events_received))
