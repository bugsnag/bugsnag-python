import platform
import time

from bugsnag import Client
from bugsnag.event import Event
from bugsnag.configuration import Configuration
from bugsnag.sessiontracker import SessionTracker
from bugsnag.utils import package_version
from tests.utils import IntegrationTest


class TestConfiguration(IntegrationTest):
    def setUp(self):
        super(TestConfiguration, self).setUp()
        self.config = Configuration()
        self.config.auto_capture_sessions = True

    def test_session_tracker_adds_session_object_to_queue(self):
        tracker = SessionTracker(self.config)
        tracker.auto_sessions = True
        tracker.start_session()
        self.assertEqual(len(tracker.session_counts), 1)
        for key, value in tracker.session_counts.items():
            self.assertEqual(value, 1)

    def test_session_tracker_send_sessions_sends_sessions(self):
        client = Client(
            auto_capture_sessions=True,
            session_endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.start_session()
        self.assertEqual(len(client.session_tracker.session_counts), 1)
        client.session_tracker.send_sessions()
        self.assertEqual(len(client.session_tracker.session_counts), 0)
        json_body = self.server.received[0]['json_body']
        self.assertTrue('app' in json_body)
        self.assertTrue('notifier' in json_body)
        self.assertTrue('device' in json_body)
        self.assertTrue('sessionCounts' in json_body)
        self.assertEqual(len(json_body['sessionCounts']), 1)

    def test_session_tracker_sets_details_from_config(self):
        client = Client(
            auto_capture_sessions=True,
            session_endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.start_session()
        client.session_tracker.send_sessions()
        json_body = self.server.received[0]['json_body']
        # Notifier properties
        notifier = json_body['notifier']
        self.assertTrue('name' in notifier)
        self.assertEqual(notifier['name'], Event.NOTIFIER_NAME)
        self.assertTrue('url' in notifier)
        self.assertEqual(notifier['url'], Event.NOTIFIER_URL)
        self.assertTrue('version' in notifier)
        notifier_version = package_version('bugsnag') or 'unknown'
        self.assertEqual(notifier['version'], notifier_version)
        # App properties
        app = json_body['app']
        self.assertTrue('releaseStage' in app)
        self.assertEqual(app['releaseStage'],
                         client.configuration.release_stage)
        self.assertTrue('version' in app)
        self.assertEqual(app['version'],
                         client.configuration.app_version)
        # Device properties
        device = json_body['device']
        self.assertTrue('hostname' in device)
        self.assertEqual(device['hostname'],
                         client.configuration.hostname)
        self.assertTrue('runtimeVersions' in device)
        self.assertEqual(device['runtimeVersions']['python'],
                         platform.python_version())

    def test_session_middleware_attaches_session_to_notification(self):
        client = Client(
            auto_capture_sessions=True,
            session_endpoint=self.server.url + '/ignore',
            endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.start_session()
        client.notify(Exception("Test"))
        while len(self.server.received) == 0:
            time.sleep(0.5)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue('session' in event)
        session = event['session']
        self.assertTrue('id' in session)
        self.assertTrue('startedAt' in session)
        self.assertTrue('events' in session)
        sesevents = session['events']
        self.assertTrue('unhandled' in sesevents)
        self.assertEqual(sesevents['unhandled'], 0)
        self.assertTrue('handled' in sesevents)
        self.assertEqual(sesevents['handled'], 1)

    def test_session_tracker_does_not_send_when_nothing_to_send(self):
        client = Client(
            api_key='fff',
            session_endpoint=self.server.url,
            asynchronous=False,
            release_stage="dev",
            notify_release_stages=["prod"],
        )
        client.session_tracker.send_sessions()
        self.assertEqual(0, len(self.server.received))

    def test_session_tracker_does_not_send_when_disabled(self):
        client = Client(
            api_key='fff',
            session_endpoint=self.server.url,
            asynchronous=False,
            release_stage="dev",
            notify_release_stages=["prod"],
        )
        client.session_tracker.start_session()
        client.session_tracker.send_sessions()
        self.assertEqual(0, len(self.server.received))

    def test_session_tracker_does_not_send_when_misconfigured(self):
        client = Client(
            api_key=None,
            session_endpoint=self.server.url,
            asynchronous=False,
            release_stage="dev",
            notify_release_stages=["prod"],
        )
        client.session_tracker.start_session()
        client.session_tracker.send_sessions()
        self.assertEqual(0, len(self.server.received))
