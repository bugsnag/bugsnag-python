from functools import wraps
from contextlib import contextmanager
import logging

from bugsnag.handlers import BugsnagHandler
from bugsnag.legacy import default_client
from bugsnag import Client, BreadcrumbType
import bugsnag

from tests.utils import IntegrationTest, ScaryException


def use_client_logger(func):
    @wraps(func)
    def wrapped(obj):
        client = Client(
            api_key='abcdef',
            endpoint=obj.server.events_url,
            session_endpoint=obj.server.sessions_url,
            asynchronous=False
        )

        handler = client.log_handler()

        with scoped_logger() as logger:
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)

            func(obj, handler, logger)

    return wrapped


@contextmanager
def scoped_logger():
    logger = logging.getLogger(__name__)

    try:
        yield logger
    finally:
        logger.handlers = []
        logger.filters = []


class HandlersTest(IntegrationTest):
    def setUp(self):
        super(HandlersTest, self).setUp()
        bugsnag.configure(
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            notify_release_stages=['dev'],
            release_stage='dev',
            asynchronous=False,
        )

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

        json_body = self.server.events_received[0]['json_body']
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

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogCRITICAL', exception['errorClass'])
        self.assertEqual('error', event['severity'])
        self.assertEqual(logging.CRITICAL,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('CRITICAL',
                         event['metaData']['extra data']['levelname'])

    def test_severity_error(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.error('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogERROR', exception['errorClass'])
        self.assertEqual('error', event['severity'])
        self.assertEqual(logging.ERROR,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('ERROR',
                         event['metaData']['extra data']['levelname'])

    def test_severity_warning(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.warning('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogWARNING', exception['errorClass'])
        self.assertEqual('warning', event['severity'])
        self.assertEqual(logging.WARNING,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('WARNING',
                         event['metaData']['extra data']['levelname'])

    def test_severity_info(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        logger.info('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogINFO', exception['errorClass'])
        self.assertEqual('info', event['severity'])
        self.assertEqual(logging.INFO,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('INFO',
                         event['metaData']['extra data']['levelname'])

    def test_levelname_message(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        class MessageFilter(logging.Filter):

            def filter(self, record):
                record.levelname = None
                return True

        handler.addFilter(MessageFilter())
        logger.info('The system is down')
        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
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
        json_body = self.server.events_received[0]['json_body']
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
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('LogOMG', exception['errorClass'])
        self.assertEqual('error', event['severity'])

    def test_exc_info(self):
        handler = BugsnagHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        try:
            raise ScaryException('Oh no')
        except Exception:
            logger.exception('The system is down')

        logger.removeHandler(handler)

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual(exception['errorClass'], 'tests.utils.ScaryException')

    def test_extra_fields(self):
        handler = BugsnagHandler(extra_fields={'fruit': ['grapes', 'pears']})
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.error('A wild tomato appeared', extra={
            'grapes': 8, 'pears': 2, 'tomatoes': 1
        })
        logger.removeHandler(handler)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['fruit'], {
            'grapes': 8, 'pears': 2
        })

    def test_client_metadata_fields(self):
        client = Client(
            api_key='abcdef',
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            asynchronous=False
        )

        handler = client.log_handler(extra_fields={
            'fruit': ['grapes', 'pears']
        })
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

        logger.error('A wild tomato appeared', extra={
            'grapes': 8, 'pears': 2, 'tomatoes': 1
        })
        logger.removeHandler(handler)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['fruit'], {
            'grapes': 8, 'pears': 2
        })

    @use_client_logger
    def test_client_message(self, handler, logger):
        logger.critical('The system is down')
        self.assertSentReportCount(1)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual('The system is down', exception['message'])

    @use_client_logger
    def test_client_severity_critical(self, handler, logger):
        logger.critical('The system is down')

        self.assertSentReportCount(1)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual('LogCRITICAL', exception['errorClass'])
        self.assertEqual('error', event['severity'])
        self.assertEqual(logging.CRITICAL,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('CRITICAL',
                         event['metaData']['extra data']['levelname'])

    @use_client_logger
    def test_client_severity_error(self, handler, logger):
        logger.error('The system is down')

        self.assertSentReportCount(1)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual('LogERROR', exception['errorClass'])
        self.assertEqual('error', event['severity'])
        self.assertEqual(logging.ERROR,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('ERROR',
                         event['metaData']['extra data']['levelname'])

    @use_client_logger
    def test_client_severity_warning(self, handler, logger):
        logger.warning('The system is down')

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual('LogWARNING', exception['errorClass'])
        self.assertEqual('warning', event['severity'])
        self.assertEqual(logging.WARNING,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('WARNING',
                         event['metaData']['extra data']['levelname'])

    @use_client_logger
    def test_client_severity_info(self, handler, logger):
        logger.info('The system is down')

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual('LogINFO', exception['errorClass'])
        self.assertEqual('info', event['severity'])
        self.assertEqual(logging.INFO,
                         event['metaData']['extra data']['levelno'])
        self.assertEqual('INFO',
                         event['metaData']['extra data']['levelname'])

    @use_client_logger
    def test_client_add_callback(self, handler, logger):

        def some_callback(record, options):
            for key in record.meals:
                options['metadata'][key] = record.meals[key]

        handler.add_callback(some_callback)
        logger.info('Everything is fine', extra={'meals': {
            'food': {'fruit': ['pear', 'grape']},
            'drinks': {'free': 'water'}
        }})

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
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
            options['metadata']['tab'] = {'key': 'value'}

        def some_other_callback(record, options):
            options['metadata']['tab2'] = {'key': 'value'}

        handler.add_callback(some_callback)
        handler.add_callback(some_other_callback)
        handler.remove_callback(some_callback)
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue('tab' not in event['metaData'])
        self.assertEqual(event['metaData']['tab2'], {
            'key': 'value'
        })

    @use_client_logger
    def test_client_clear_callbacks(self, handler, logger):

        def some_callback(record, options):
            options['metadata']['tab'] = {'key': 'value'}

        def some_other_callback(record, options):
            options['metadata']['tab2'] = {'key': 'value'}

        handler.add_callback(some_callback)
        handler.add_callback(some_other_callback)
        handler.clear_callbacks()
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue('tab' not in event['metaData'])
        self.assertTrue('tab2' not in event['metaData'])

    @use_client_logger
    def test_client_crashing_callback(self, handler, logger):

        def some_callback(record, options):
            options['metadata']['tab'] = {'key': 'value'}
            raise ScaryException('Oh dear')

        def some_other_callback(record, options):
            options['metadata']['tab']['key2'] = 'other value'

        handler.add_callback(some_callback)
        handler.add_callback(some_other_callback)
        logger.info('Everything is fine')

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
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
        json_body = self.server.events_received[0]['json_body']
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
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual(exception['errorClass'], 'LogINFO')
        self.assertEqual(exception['message'], 'Everything is fine')
        self.assertEqual(event['metaData']['custom'],
                         {'exception': 'metadata'})

    @use_client_logger
    def test_logging_grouping_hash(self, handler, logger):
        logger.info("This happened", extra={'groupingHash': '<hash value>'})

        self.assertSentReportCount(1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual(exception['message'], 'This happened')
        self.assertEqual(event['groupingHash'], '<hash value>')

    @use_client_logger
    def test_log_filter_leaves_breadcrumbs_for_logs_below_report_level(
        self,
        handler,
        logger
    ):
        logger.addFilter(handler.leave_breadcrumbs)
        handler.setLevel(logging.ERROR)

        logger.info('Everything is fine')

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 1

        breadcrumb = handler.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'Everything is fine'
        assert breadcrumb.type == BreadcrumbType.LOG
        assert breadcrumb.metadata == {'logLevel': 'INFO'}

        logger.error('Everything is not fine')

        assert self.sent_report_count == 1

        # we expect 2 breadcrumbs - one from the 'info' log above and one from
        # the notify caused by the 'error' log
        assert len(handler.client.configuration.breadcrumbs) == 2

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        assert exception['errorClass'] == 'LogERROR'
        assert exception['message'] == 'Everything is not fine'

        breadcrumb = handler.client.configuration.breadcrumbs[1]
        assert breadcrumb.message == 'LogERROR'
        assert breadcrumb.type == BreadcrumbType.ERROR
        assert breadcrumb.metadata == {
            'errorClass': 'LogERROR',
            'message': 'Everything is not fine',
            'severity': 'error',
            'unhandled': False,
        }

    @use_client_logger
    def test_log_filter_does_not_leave_breadcrumbs_for_logs_below_its_level(
        self,
        handler,
        logger
    ):
        logger.addFilter(handler.leave_breadcrumbs)
        handler.setLevel(logging.ERROR)

        handler.client.configuration.configure(
            breadcrumb_log_level=logging.WARN
        )

        logger.info('Everything is fine')

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 0

        logger.warning('Everything might be fine')

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 1

        breadcrumb = handler.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'Everything might be fine'
        assert breadcrumb.type == BreadcrumbType.LOG
        assert breadcrumb.metadata == {'logLevel': 'WARNING'}

    @use_client_logger
    def test_log_filter_does_not_leave_breadcrumbs_when_bugsnag_create_breadcrumb_is_false(  # noqa: E501
        self,
        handler,
        logger
    ):
        logger.addFilter(handler.leave_breadcrumbs)
        handler.setLevel(logging.ERROR)

        logger.info(
            'Everything is fine',
            extra={'bugsnag_create_breadcrumb': False}
        )

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 0

        logger.info(
            'Everything is fine',
            extra={'bugsnag_create_breadcrumb': True}
        )

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 1

        breadcrumb = handler.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'Everything is fine'
        assert breadcrumb.type == BreadcrumbType.LOG
        assert breadcrumb.metadata == {'logLevel': 'INFO'}

        logger.info('Everything is fine')

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 2

        breadcrumb = handler.client.configuration.breadcrumbs[1]
        assert breadcrumb.message == 'Everything is fine'
        assert breadcrumb.type == BreadcrumbType.LOG
        assert breadcrumb.metadata == {'logLevel': 'INFO'}

    @use_client_logger
    def test_log_filter_does_not_leave_breadcrumbs_when_log_breadcrumbs_are_disabled(  # noqa: E501
        self,
        handler,
        logger
    ):
        logger.addFilter(handler.leave_breadcrumbs)
        handler.setLevel(logging.ERROR)
        handler.client.configuration.configure(enabled_breadcrumb_types=[])

        logger.info('Everything is fine')

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 0

        handler.client.configuration.configure(
            enabled_breadcrumb_types=[BreadcrumbType.LOG]
        )

        logger.info('Everything is fine')

        assert self.sent_report_count == 0
        assert len(handler.client.configuration.breadcrumbs) == 1

        breadcrumb = handler.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'Everything is fine'
        assert breadcrumb.type == BreadcrumbType.LOG
        assert breadcrumb.metadata == {'logLevel': 'INFO'}

    def test_log_filter_leaves_breadcrumbs_when_manually_constructed(self):
        default_client.configuration.max_breadcrumbs = 25

        with scoped_logger() as logger:
            handler = BugsnagHandler()
            logger.addHandler(handler)
            logger.addFilter(handler.leave_breadcrumbs)

            logger.setLevel(logging.INFO)
            handler.setLevel(logging.ERROR)

            logger.info('Everything is fine')

            assert self.sent_report_count == 0
            assert len(default_client.configuration.breadcrumbs) == 1

            breadcrumb = default_client.configuration.breadcrumbs[0]
            assert breadcrumb.message == 'Everything is fine'
            assert breadcrumb.type == BreadcrumbType.LOG
            assert breadcrumb.metadata == {'logLevel': 'INFO'}

            logger.error('Everything is not fine')

            assert self.sent_report_count == 1

            # we expect 2 breadcrumbs - one from the 'info' log above and one
            # from the notify caused by the 'error' log
            assert len(default_client.configuration.breadcrumbs) == 2

            json_body = self.server.events_received[0]['json_body']
            event = json_body['events'][0]
            exception = event['exceptions'][0]

            assert exception['errorClass'] == 'LogERROR'
            assert exception['message'] == 'Everything is not fine'

            breadcrumb = default_client.configuration.breadcrumbs[1]
            assert breadcrumb.message == 'LogERROR'
            assert breadcrumb.type == BreadcrumbType.ERROR
            assert breadcrumb.metadata == {
                'errorClass': 'LogERROR',
                'message': 'Everything is not fine',
                'severity': 'error',
                'unhandled': False,
            }

    def test_log_filter_leaves_breadcrumbs_when_handler_has_no_level(self):
        default_client.configuration.max_breadcrumbs = 25

        with scoped_logger() as logger:
            handler = BugsnagHandler()
            logger.addFilter(handler.leave_breadcrumbs)
            logger.setLevel(logging.DEBUG)

            logger.info('Everything is fine')

            assert self.sent_report_count == 0
            assert len(default_client.configuration.breadcrumbs) == 1

            breadcrumb = default_client.configuration.breadcrumbs[0]
            assert breadcrumb.message == 'Everything is fine'
            assert breadcrumb.type == BreadcrumbType.LOG
            assert breadcrumb.metadata == {'logLevel': 'INFO'}

            logger.error('Everything is not fine')

            assert self.sent_report_count == 0
            assert len(default_client.configuration.breadcrumbs) == 2

            breadcrumb = default_client.configuration.breadcrumbs[1]
            assert breadcrumb.message == 'Everything is not fine'
            assert breadcrumb.type == BreadcrumbType.LOG
            assert breadcrumb.metadata == {'logLevel': 'ERROR'}
