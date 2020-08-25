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
        self.assertEqual(event['metaData']['environment']['PATH_INFO'],
                         '/beans')
        runtime_versions = event['device']['runtimeVersions']
        self.assertEqual(runtime_versions['bottle'], '0.12.18')

    def test_disable_environment(self):
        bugsnag.configure(send_environment=False)

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
        assert 'environment' not in metadata

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
        self.assertEqual(event['metaData']['environment']['PATH_INFO'],
                         '/berries/red')
        runtime_versions = event['device']['runtimeVersions']
        self.assertEqual(runtime_versions['bottle'], bottle.__version__)
