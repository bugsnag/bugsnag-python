from webtest import TestApp
import bottle
from bottle import route, template
import bugsnag
from bugsnag.wsgi.middleware import BugsnagMiddleware

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

        self.assertRaises(Exception, lambda: app.get('/beans'))
        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertTrue(event['unhandled'])
        self.assertEqual(event['context'], 'GET /beans')
        self.assertEqual(event['exceptions'][0]['errorClass'], 'Exception')
        self.assertEqual(event['exceptions'][0]['message'], 'oh no!')
        runtime_versions = event['device']['runtimeVersions']
        self.assertEqual(runtime_versions['bottle'], '0.12.18')
        assert 'environment' not in event['metaData']

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
