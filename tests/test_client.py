import sys

from bugsnag import Client, Configuration
from tests.utils import IntegrationTest


class ClientTest(IntegrationTest):
    def setUp(self):
        super(ClientTest, self).setUp()

        self.client = Client(api_key='testing client key',
                             use_ssl=False, endpoint=self.server.address,
                             asynchronous=False)

    # Initialisation

    def test_init_no_configuration(self):
        client = Client()
        self.assertTrue(isinstance(client.configuration, Configuration))

    def test_init_configuration(self):
        configuration = Configuration()
        client = Client(configuration=configuration)

        self.assertEqual(client.configuration, configuration)

    def test_init_options(self):
        client = Client(api_key='testing client key')
        self.assertEqual(client.configuration.api_key, 'testing client key')

    # Sending Notification

    def test_notify_exception(self):
        self.client.notify(Exception('Testing Notify'))

        self.assertEqual(len(self.server.received), 1)

    def test_notify_exc_info(self):
        try:
            raise Exception('Testing Notify EXC Info')
        except Exception:
            self.client.notify_exc_info(*sys.exc_info())

        self.assertEqual(len(self.server.received), 1)

    # Context

    def test_notify_context(self):
        with self.client.context():
            raise Exception('Testing Notify Context')

        self.assertEqual(len(self.server.received), 1)

    def test_notify_context_swallow(self):
        with self.assertRaises(Exception):
            with self.client.context(swallow=False):
                raise Exception('Testing Notify Context')

        self.assertEqual(len(self.server.received), 1)

    def test_notify_context_options(self):
        with self.client.context(section={'key':'value'}):
            raise Exception('Testing Notify Context')

        self.assertEqual(len(self.server.received), 1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['section'], {
            'key': 'value'
        })
