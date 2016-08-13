import unittest

import bugsnag
from tests.utils import FakeBugsnagServer, ScaryException
from tests.fixtures import samples


class TestBugsnag(unittest.TestCase):

    def setUp(self):
        """
        Initializes the server. The server must be shut down prior to
        evaluating request information.
        """
        self.server = FakeBugsnagServer()
        bugsnag.configure(use_ssl=False,
                          endpoint=self.server.url(),
                          api_key='tomatoes',
                          notify_release_stages=['dev'],
                          release_stage='dev',
                          async=False)

    def shutDown(self):
        bugsnag.configuration = bugsnag.Configuration()
        bugsnag.configuration.api_key = 'some key'

    def test_notify_method(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        request = self.server.received[0]
        self.assertEqual('POST', request['method'])

    def test_notify_request_count(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        self.assertEqual(1, len(self.server.received))

    def test_notify_configured_api_key(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        self.assertEqual('tomatoes', json_body['apiKey'])

    def test_notify_configured_release_stage(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('dev', event['releaseStage'])

    def test_notify_default_severity(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('warning', event['severity'])

    def test_notify_override_severity(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       severity='info')
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('info', event['severity'])

    def test_notify_configured_app_version(self):
        bugsnag.configure(app_version='343.2.10')
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('343.2.10', event['appVersion'])

    def test_notify_override_context(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       context='/some/path')
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('/some/path', event['context'])

    def test_notify_override_grouping_hash(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       grouping_hash='Callout errors')
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('Callout errors', event['groupingHash'])

    def test_notify_override_user(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       user={'name': 'bob',
                             'email': 'mcbob@example.com',
                             'id': '542347329'})
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('bob', event['user']['name'])
        self.assertEqual('542347329', event['user']['id'])
        self.assertEqual('mcbob@example.com', event['user']['email'])

    def test_notify_configured_hostname(self):
        bugsnag.configure(hostname='I_AM_ROOT')
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('I_AM_ROOT', event['device']['hostname'])

    def test_notify_override_metadata_sections(self):
        bugsnag.add_metadata_tab('food', {'beans': 3, 'corn': 'purple'})
        bugsnag.notify(ScaryException('unexpected failover'),
                       meta_data={'food': {'beans': 5},
                                  'skills': {'spear': 6}})
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(6, event['metaData']['skills']['spear'])
        self.assertEqual('purple', event['metaData']['food']['corn'])
        self.assertEqual(5, event['metaData']['food']['beans'])

    def test_notify_configured_metadata_sections(self):
        bugsnag.add_metadata_tab('food', {'beans': 3, 'corn': 'purple'})
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('purple', event['metaData']['food']['corn'])
        self.assertEqual(3, event['metaData']['food']['beans'])

    def test_notify_configured_lib_root(self):
        bugsnag.configure(lib_root='/the/basement')
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('/the/basement', event['libRoot'])

    def test_notify_configured_project_root(self):
        bugsnag.configure(project_root='/the/basement')
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('/the/basement', event['projectRoot'])

    def test_notify_override_deprecated_user_id(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       user_id='542347329')
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('542347329', event['user']['id'])

    def test_notify_override_api_key(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       api_key='gravy!')
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        self.assertEqual('gravy!', json_body['apiKey'])

    def test_notify_payload_version(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('2', event['payloadVersion'])

    def test_notify_error_class(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])

    def test_notify_error_message(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('unexpected failover', exception['message'])

    def test_notify_stacktrace(self):
        samples.call_bugsnag_nested()
        self.server.shutdown()
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        frames = event['exceptions'][0]['stacktrace']

        self.assertTrue(frames[0]['file'].endswith('fixtures/samples.py'))
        self.assertEqual(11, frames[0]['lineNumber'])
        self.assertEqual('chain_3', frames[0]['method'])
        self.assertEqual('chain_3', frames[0]['method'])
        self.assertEqual('', frames[0]['code']['7'])
        self.assertEqual('', frames[0]['code']['8'])
        self.assertEqual('def chain_3():', frames[0]['code']['9'])
        self.assertEqual('    import bugsnag', frames[0]['code']['10'])
        self.assertEqual("    bugsnag.notify(Exception('oh noooo'))",
                         frames[0]['code']['11'])

        self.assertTrue(frames[1]['file'].endswith('fixtures/samples.py'))
        self.assertEqual(6, frames[1]['lineNumber'])
        self.assertEqual('chain_2', frames[1]['method'])
        self.assertEqual('', frames[1]['code']['4'])
        self.assertEqual('def chain_2():', frames[1]['code']['5'])
        self.assertEqual('    chain_3()', frames[1]['code']['6'])
        self.assertEqual('', frames[1]['code']['7'])
        self.assertEqual('', frames[1]['code']['8'])

        self.assertTrue(frames[2]['file'].endswith('fixtures/samples.py'))
        self.assertEqual(2, frames[2]['lineNumber'])
        self.assertEqual('def call_bugsnag_nested():', frames[2]['code']['1'])
        self.assertEqual('    chain_2()', frames[2]['code']['2'])
        self.assertEqual('', frames[2]['code']['3'])
        self.assertEqual('', frames[2]['code']['4'])
