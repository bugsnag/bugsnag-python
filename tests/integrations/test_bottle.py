from webtest import TestApp
import bottle
from bottle import route, template
import bugsnag
from bugsnag.wsgi.middleware import BugsnagMiddleware
import pytest
from tests.utils import IntegrationTest


class TestBottle(IntegrationTest):
    def setUp(self):
        super(TestBottle, self).setUp()
        bugsnag.configure(endpoint=self.server.url,
                          session_endpoint=self.server.url,
                          auto_capture_sessions=False,
                          api_key='3874876376238728937',
                          asynchronous=False)

    def test_routing_error(self):
        @route('/beans')
        def index():
            raise Exception('oh no!')

        app = bottle.app()
        app.catchall = False
        app = TestApp(BugsnagMiddleware(app))

        self.assertRaises(Exception, lambda: app.get('/beans?password=123'))
        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertTrue(event['unhandled'])
        self.assertEqual(event['context'], 'GET /beans')
        self.assertEqual(event['exceptions'][0]['errorClass'], 'Exception')
        self.assertEqual(event['exceptions'][0]['message'], 'oh no!')
        runtime_versions = event['device']['runtimeVersions']
        assert runtime_versions['bottle'] == bottle.__version__
        assert 'environment' not in event['metaData']

        assert event['metaData']['request']['url'] == 'http://localhost/beans'
        assert event['metaData']['request']['params'] == {
            'password': '[FILTERED]'
        }

    def test_enable_environment(self):
        bugsnag.configure(send_environment=True)

        @route('/beans')
        def index():
            raise Exception('oh no!')

        app = bottle.app()
        app.catchall = False
        app = TestApp(BugsnagMiddleware(app))

        self.assertRaises(Exception, lambda: app.get('/beans'))
        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        metadata = payload['events'][0]['metaData']
        self.assertEqual(metadata['environment']['PATH_INFO'], '/beans')

    def test_template_error(self):
        @route('/berries/<variety>')
        def index(variety):
            return template('{{type1}} {{type2}}', type1=variety)

        app = bottle.app()
        app.catchall = False
        app = TestApp(BugsnagMiddleware(app))

        self.assertRaises(Exception, lambda: app.get('/berries/red'))
        self.assertEqual(1, len(self.server.received))

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertTrue(event['unhandled'])
        self.assertEqual(event['context'], 'GET /berries/red')
        self.assertEqual(event['exceptions'][0]['errorClass'], 'NameError')
        self.assertEqual(event['exceptions'][0]['message'],
                         "name 'type2' is not defined")
        assert 'environment' not in event['metaData']
        runtime_versions = event['device']['runtimeVersions']
        self.assertEqual(runtime_versions['bottle'], bottle.__version__)

    def test_feature_flags_dont_leak_between_requests(self):
        count = 0

        def other_func():
            nonlocal count
            count += 1
            bugsnag.add_feature_flag('b', count)

            if count > 4:
                bugsnag.clear_feature_flags()

            raise Exception('oh no!')

        @route('/')
        def index():
            nonlocal count
            count += 1
            bugsnag.add_feature_flag('a', count)

            other_func()

        app = bottle.app()
        app.catchall = False
        app = TestApp(BugsnagMiddleware(app))

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 1

        payload = self.server.received[0]['json_body']
        exception = payload['events'][0]['exceptions'][0]
        feature_flags = payload['events'][0]['featureFlags']

        assert exception['errorClass'] == 'Exception'
        assert exception['message'] == 'oh no!'
        assert exception['stacktrace'][0]['method'] == 'other_func'
        assert exception['stacktrace'][1]['method'] == 'index'

        assert feature_flags == [
            {'name': 'a', 'variant': '1'},
            {'name': 'b', 'variant': '2'}
        ]

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 2

        payload = self.server.received[1]['json_body']
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == [
            {'name': 'a', 'variant': '3'},
            {'name': 'b', 'variant': '4'}
        ]

        with pytest.raises(Exception):
            app.get('/')

        assert self.sent_report_count == 3

        payload = self.server.received[2]['json_body']
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == []
