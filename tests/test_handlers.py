import logging
import sys

from six import u

from bugsnag.handlers import BugsnagHandler
import bugsnag

from tests.utils import IntegrationTest


class HandlerTest(IntegrationTest):

    def setUp(self):
        super(HandlerTest, self).setUp()
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.address,
                          api_key='tomatoes',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          asynchronous=False)
        bugsnag.logger.setLevel(logging.INFO)

    def tearDown(self):
        super(HandlerTest, self).tearDown()
        bugsnag.logger.setLevel(logging.CRITICAL)

    def test_message(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.critical('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('The system is down', exception['message'])

    def test_severity_critical(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.critical('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogCRITICAL', exception['errorClass'])
        self.assertEqual('error', event['severity'])
        self.assertEqual(logging.CRITICAL,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual(u('CRITICAL'),
                         event['metaData']['extra data']['levelname'])

    def test_severity_error(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.error('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogERROR', exception['errorClass'])
        self.assertEqual('error', event['severity'])
        self.assertEqual(logging.ERROR,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual(u('ERROR'),
                         event['metaData']['extra data']['levelname'])

    def test_severity_warning(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.warning('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogWARNING', exception['errorClass'])
        self.assertEqual('warning', event['severity'])
        self.assertEqual(logging.WARNING,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual(u('WARNING'),
                         event['metaData']['extra data']['levelname'])

    def test_severity_info(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.info('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogINFO', exception['errorClass'])
        self.assertEqual('info', event['severity'])
        self.assertEqual(logging.INFO,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual(u('INFO'),
                         event['metaData']['extra data']['levelname'])

    def test_exc_info_api_key(self):
        handler = BugsnagHandler(api_key='new news')
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        try:
            raise Exception('Oh no')
        except Exception:
            logger.error('The system is down', exc_info=sys.exc_info)

        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        self.assertEqual('new news', json_body['apiKey'])

    def test_extra_fields(self):

        class FruitFilter(logging.Filter):

            def filter(self, record):
                record.grapes = 8
                record.pears = 2
                record.apricots = 90
                return True

        handler = BugsnagHandler(api_key='new news',
                                 extra_fields={'fruit': ['grapes', 'pears']})
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        logger.addFilter(FruitFilter())

        logger.error('A wild tomato appeared')
        logger.removeHandler(handler)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['fruit'], {
            'grapes': 8, 'pears': 2
        })
