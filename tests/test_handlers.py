from functools import wraps
import logging

from six import u

from bugsnag.handlers import BugsnagHandler
from bugsnag import Client
import bugsnag

from tests.utils import IntegrationTest, ScaryException


def use_client_logger(func):
    @wraps(func)
    def wrapped(obj):
        client = Client(use_ssl=False,
                        endpoint=obj.server.address,
                        api_key='tomatoes',
                        asynchronous=False)
        handler = client.log_handler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        try:
            func(obj, handler, logger)
        finally:
            logger.removeHandler(handler)

    return wrapped


class HandlersTest(IntegrationTest):

    def setUp(self):
        super(HandlersTest, self).setUp()
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.address,
                          api_key='tomatoes',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          asynchronous=False)
        bugsnag.logger.setLevel(logging.INFO)

    def tearDown(self):
        super(HandlersTest, self).tearDown()
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

    def test_levelname_message(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        class MessageFilter(logging.Filter):

            def filter(self, record):
                record.levelname = None
                return True

        handler.addFilter(MessageFilter())
        logger.info('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogMessage', exception['errorClass'])

    def test_custom_level(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.log(341, 'The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogLevel 341', exception['errorClass'])

    def test_custom_levelname(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        logging.addLevelName(402, 'OMG')

        logger.log(402, 'The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogOMG', exception['errorClass'])
        self.assertEqual('error', event['severity'])

    def test_exc_info_api_key(self):
        handler = BugsnagHandler(api_key='new news')
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        try:
            raise ScaryException('Oh no')
        except Exception:
            logger.exception('The system is down')

        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        headers = self.server.received[0]['headers']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('new news', headers['Bugsnag-Api-Key'])
        self.assertEqual(exception['errorClass'], 'tests.utils.ScaryException')

    def test_extra_fields(self):
        handler = BugsnagHandler(api_key='new news',
                                 extra_fields={'fruit': ['grapes', 'pears']})
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.error('A wild tomato appeared', extra={
            'grapes': 8, 'pears': 2, 'tomatoes': 1
        })
        logger.removeHandler(handler)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['fruit'], {
            'grapes': 8, 'pears': 2
        })

    def test_client_metadata_fields(self):
        client = Client(use_ssl=False,
                        endpoint=self.server.address,
                        api_key='new news',
                        asynchronous=False)
        handler = client.log_handler(extra_fields={
            'fruit': ['grapes', 'pears']
        })
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.error('A wild tomato appeared', extra={
            'grapes': 8, 'pears': 2, 'tomatoes': 1
        })
        logger.removeHandler(handler)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['fruit'], {
            'grapes': 8, 'pears': 2
        })

    @use_client_logger
    def test_client_message(self, handler, logger):
        logger.critical('The system is down')
        self.assertSentReportCount(1)

        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual('The system is down', exception['message'])

    @use_client_logger
    def test_client_severity_critical(self, handler, logger):
        logger.critical('The system is down')

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

    @use_client_logger
    def test_client_severity_error(self, handler, logger):
        logger.error('The system is down')

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

    @use_client_logger
    def test_client_severity_warning(self, handler, logger):
        logger.warning('The system is down')

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

    @use_client_logger
    def test_client_severity_info(self, handler, logger):
        logger.info('The system is down')

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

    @use_client_logger
    def test_client_add_callback(self, handler, logger):

        def some_callback(record, options):
            for key in record.meals:
                options['meta_data'][key] = record.meals[key]

        handler.add_callback(some_callback)
        logger.info('Everything is fine', extra={'meals': {
            'food': {'fruit': ['pear', 'grape']},
            'drinks': {'free': 'water'}
        }})

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['food'], {
            'fruit': ['pear', 'grape']
        })
        self.assertEqual(event['metaData']['drinks'], {
            'free': 'water'
        })

    @use_client_logger
    def test_client_remove_callback(self, handler, logger):

        def some_callback(record, options):
            options['meta_data']['tab'] = {'key': 'value'}

        def some_other_callback(record, options):
            options['meta_data']['tab2'] = {'key': 'value'}

        handler.add_callback(some_callback)
        handler.add_callback(some_other_callback)
        handler.remove_callback(some_callback)
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue('tab' not in event['metaData'])
        self.assertEqual(event['metaData']['tab2'], {
            'key': 'value'
        })

    @use_client_logger
    def test_client_clear_callbacks(self, handler, logger):

        def some_callback(record, options):
            options['meta_data']['tab'] = {'key': 'value'}

        def some_other_callback(record, options):
            options['meta_data']['tab2'] = {'key': 'value'}

        handler.add_callback(some_callback)
        handler.add_callback(some_other_callback)
        handler.clear_callbacks()
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue('tab' not in event['metaData'])
        self.assertTrue('tab2' not in event['metaData'])

    @use_client_logger
    def test_client_crashing_callback(self, handler, logger):

        def some_callback(record, options):
            options['meta_data']['tab'] = {'key': 'value'}
            raise ScaryException('Oh dear')

        def some_other_callback(record, options):
            options['meta_data']['tab']['key2'] = 'other value'

        handler.add_callback(some_callback)
        handler.add_callback(some_other_callback)
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['tab'], {
            'key': 'value', 'key2': 'other value'
        })

    @use_client_logger
    def test_client_callback_exception(self, handler, logger):

        def exception_replacing_callback(record, options):
            options['exception'] = ScaryException('replacement')

        handler.add_callback(exception_replacing_callback)
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual(exception['errorClass'], 'tests.utils.ScaryException')
        self.assertEqual(exception['message'], 'replacement')

    @use_client_logger
    def test_client_callback_exception_metadata(self, handler, logger):

        def exception_replacing_callback(record, options):
            options['exception'] = 'metadata'

        handler.add_callback(exception_replacing_callback)
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual(exception['errorClass'], 'LogINFO')
        self.assertEqual(exception['message'], 'Everything is fine')
        self.assertEqual(event['metaData']['custom'],
                         {'exception': 'metadata'})
