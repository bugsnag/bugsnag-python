from bugsnag import Configuration
from bugsnag.delivery import (RequestsDelivery, create_default_delivery)

from tests.utils import IntegrationTest


class RequestsDeliveryTest(IntegrationTest):
    def setUp(self):
        super(RequestsDeliveryTest, self).setUp()

        self.config = Configuration()
        self.config.configure(
            api_key='abc',
            asynchronous=False,
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
        )

    def test_requests_delivery(self):
        RequestsDelivery().deliver(self.config, '{"legit": 4}')

        self.assertSentReportCount(1)

        request = self.server.events_received[0]

        self.assertEqual(request['json_body'], {"legit": 4})
        self.assertEqual(
            request['headers']['Content-Type'],
            'application/json'
        )

    def test_requests_delivery_full_url(self):
        RequestsDelivery().deliver(self.config, '{"good": 5}')

        self.assertSentReportCount(1)

        request = self.server.events_received[0]

        self.assertEqual(request['json_body'], {'good': 5})

    def test_create_default_delivery(self):
        delivery = create_default_delivery()

        self.assertTrue(isinstance(delivery, RequestsDelivery))
