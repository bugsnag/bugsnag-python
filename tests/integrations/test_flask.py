import json
import re
from flask import Flask
from bugsnag.flask import handle_exceptions
import bugsnag.event
from bugsnag.breadcrumbs import BreadcrumbType
from tests.utils import IntegrationTest


class SentinelError(RuntimeError):
    pass


class TestFlask(IntegrationTest):

    def setUp(self):
        super(TestFlask, self).setUp()
        bugsnag.configure(endpoint=self.server.url,
                          api_key='3874876376238728937',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          asynchronous=False,
                          max_breadcrumbs=25)

    def test_bugsnag_middleware_working(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            return "OK"

        handle_exceptions(app)

        resp = app.test_client().get('/hello')
        self.assertEqual(resp.data, b'OK')

        self.assertEqual(0, len(self.server.received))

    def test_bugsnag_crash(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().get('/hello?password=secret')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'test_flask.SentinelError')
        assert event['metaData']['request']['url'] == 'http://localhost/hello'
        assert event['metaData']['request']['params'] == {}
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {'to': '/hello'}
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_enable_environment(self):
        bugsnag.configure(send_environment=True)

        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().get('/hello')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['environment']['REMOTE_ADDR'],
                         '127.0.0.1')

    def test_bugsnag_notify(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            bugsnag.notify(SentinelError("oops"))
            return "OK"

        handle_exceptions(app)
        app.test_client().get('/hello')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        self.assertEqual(payload['events'][0]['metaData']['request']['url'],
                         'http://localhost/hello')

    def test_bugsnag_custom_data(self):
        metadata = [{"hello": {"world": "once"}},
                    {"again": {"hello": "world"}}]

        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            bugsnag.configure_request(metadata=metadata.pop())
            raise SentinelError("oops")

        handle_exceptions(app)
        with app.test_client() as client:
            client.get('/hello')
            client.get('/hello')

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData'].get('hello'), None)
        self.assertEqual(event['metaData']['again']['hello'], 'world')

        payload = self.server.received[1]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['hello']['world'], 'once')
        self.assertEqual(event['metaData'].get('again'), None)
        self.assertEqual(2, len(self.server.received))

    def test_bugsnag_includes_posted_json_data(self):
        app = Flask("bugsnag")

        @app.route("/ajax", methods=["POST"])
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        body = {
            '_links': {
                'self': {
                    'href': 'http://example.com/api/resource/a'
                }
            },
            'id': 'res-a',
            'name': 'Resource A'
        }
        app.test_client().post(
            '/ajax', data=json.dumps(body),
            content_type='application/hal+json')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'test_flask.SentinelError')
        self.assertEqual(event['metaData']['request']['url'],
                         'http://localhost/ajax')
        self.assertEqual(event['metaData']['request']['data'], body)

    def test_bugsnag_includes_request_when_json_malformed(self):
        app = Flask("bugsnag")

        @app.route("/ajax", methods=["POST"])
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().post(
            '/ajax', data='{"key": "value"', content_type='application/json')
        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'test_flask.SentinelError')
        self.assertEqual(event['metaData']['request']['url'],
                         'http://localhost/ajax')
        self.assertEqual(event['metaData']['request']['data']['body'],
                         '{"key": "value"')

    def test_bugsnag_add_metadata_tab(self):
        app = Flask("bugsnag")

        @app.route("/form", methods=["PUT"])
        def hello():
            bugsnag.add_metadata_tab("account", {"id": 1, "premium": True})
            bugsnag.add_metadata_tab("account", {"premium": False})
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().put(
            '/form', data='_data', content_type='application/octet-stream')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['metaData']['account']['premium'], False)
        self.assertEqual(event['metaData']['account']['id'], 1)

    def test_bugsnag_includes_unknown_content_type_posted_data(self):
        app = Flask("bugsnag")

        @app.route("/form", methods=["PUT"])
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().put(
            '/form', data='_data', content_type='application/octet-stream')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'test_flask.SentinelError')
        self.assertEqual(event['metaData']['request']['url'],
                         'http://localhost/form')
        body = event['metaData']['request']['data']['body']
        self.assertTrue('_data' in body)

    def test_bugsnag_notify_with_custom_context(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            bugsnag.notify(SentinelError("oops"),
                           context="custom_context_event_testing")
            return "OK"

        handle_exceptions(app)
        app.test_client().get('/hello')

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        self.assertEqual(payload['events'][0]['context'],
                         'custom_context_event_testing')

    def test_flask_intergration_includes_middleware_severity(self):
        app = Flask("bugsnag")

        @app.route("/test")
        def test():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().get("/test")

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertTrue(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            "type": "unhandledExceptionMiddleware",
            "attributes": {
                "framework": "Flask"
            }
        })

    def test_appends_framework_version(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        app.test_client().get('/hello')

        self.assertEqual(len(self.server.received), 1)

        payload = self.server.received[0]['json_body']
        device_data = payload['events'][0]['device']

        self.assertEquals(len(device_data['runtimeVersions']), 2)
        self.assertTrue(re.match(r'\d+\.\d+\.\d+',
                                 device_data['runtimeVersions']['python']))
        self.assertTrue(re.match(r'\d+\.\d+\.\d+',
                                 device_data['runtimeVersions']['flask']))

    def test_read_request_in_callback(self):
        def callback(event):
            event.set_user(id=event.request.args['id'])
            return True

        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            raise SentinelError("oops")

        bugsnag.before_notify(callback)
        handle_exceptions(app)
        app.test_client().get('/hello?id=foo')

        assert len(self.server.received) == 1
        payload = self.server.received[0]['json_body']
        assert payload['events'][0]['user']['id'] == 'foo'

    def test_bugsnag_middleware_leaves_breadcrumb_with_referer(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            raise SentinelError("oops")

        handle_exceptions(app)
        headers = {'referer': 'http://localhost/hi?password=hunter2'}
        app.test_client().get('/hello', headers=headers)

        self.assertEqual(1, len(self.server.received))
        payload = self.server.received[0]['json_body']
        event = payload['events'][0]
        self.assertEqual(event['exceptions'][0]['errorClass'],
                         'test_flask.SentinelError')
        self.assertEqual(event['metaData']['request']['url'],
                         'http://localhost/hello')
        assert 'environment' not in event['metaData']

        breadcrumbs = payload['events'][0]['breadcrumbs']

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]['name'] == 'http request'
        assert breadcrumbs[0]['metaData'] == {
            'to': '/hello',
            'from': 'http://localhost/hi'
        }
        assert breadcrumbs[0]['type'] == BreadcrumbType.NAVIGATION.value

    def test_chained_exceptions(self):
        app = Flask("bugsnag")

        @app.route("/hello")
        def hello():
            try:
                raise SentinelError("oops")
            except SentinelError:
                1 / 0

        handle_exceptions(app)
        app.test_client().get('/hello')

        assert self.sent_report_count == 1

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]

        assert len(event['exceptions']) == 2

        exception1 = event['exceptions'][0]
        exception2 = event['exceptions'][1]

        assert exception1['errorClass'] == 'ZeroDivisionError'
        assert exception1['message'] == 'division by zero'

        assert exception2['errorClass'] == 'test_flask.SentinelError'
        assert exception2['message'] == 'oops'
