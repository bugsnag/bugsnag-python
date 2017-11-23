import sys
import time

from bugsnag import Client
from bugsnag.notification import Notification
from bugsnag.configuration import Configuration
from bugsnag.sessiontracker import SessionTracker
from bugsnag.utils import ThreadLocals, package_version
from tests.utils import IntegrationTest, ScaryException

class TestConfiguration(IntegrationTest):
    def setUp(self):
        super(TestConfiguration, self).setUp()
        self.config = Configuration()
        self.config.track_sessions = True

    def test_session_tracker_doesnt_create_session_object_if_disabled(self):
        config = Configuration()
        config.track_sessions = False
        tracker = SessionTracker(config)
        tracker.create_session()
        self.assertEqual(tracker.delivery_queue.qsize(), 0)

    def test_session_tracker_adds_session_object_to_queue(self):
        tracker = SessionTracker(self.config)
        tracker.create_session()
        self.assertEqual(tracker.delivery_queue.qsize(), 1)
        session = tracker.delivery_queue.get(False)
        self.assertTrue('id' in session)
        self.assertTrue('user' in session)
        self.assertTrue('startedAt' in session)
        self.assertEqual(session['user'], {})

    def test_session_tracker_stores_user_object(self):
        tracker = SessionTracker(self.config)
        tracker.create_session({"id": "userid", "attr": {"name": "James", "job": "Spy"}})
        self.assertEqual(tracker.delivery_queue.qsize(), 1)
        session = tracker.delivery_queue.get(False)
        self.assertTrue('user' in session)
        self.assertEqual(session['user'], {"id": "userid", "attr": {"name": "James", "job": "Spy"}})

    def test_session_tracker_stores_session_in_threadlocals(self):
        locs = ThreadLocals.get_instance()
        tracker = SessionTracker(self.config)
        tracker.create_session()
        session = locs.get_item('bugsnag-session')
        self.assertTrue('id' in session)
        self.assertFalse('user' in session)
        self.assertTrue('startedAt' in session)
        self.assertTrue('events' in session)
        self.assertTrue('handled' in session['events'])
        self.assertTrue('unhandled' in session['events'])
        self.assertEqual(session['events']['handled'], 0)
        self.assertEqual(session['events']['unhandled'], 0)

    def test_session_tracker_calls_user_callback(self):
        tracker = SessionTracker(self.config)
        def user_callback():
            return {"id": "userid", "attr": {"name": "Jason", "job": "Spy"}}
        tracker.set_user_callback(user_callback)
        tracker.create_session()
        self.assertEqual(tracker.delivery_queue.qsize(), 1)
        session = tracker.delivery_queue.get(False)
        self.assertTrue('user' in session)
        self.assertEqual(session['user'], {"id": "userid", "attr": {"name": "Jason", "job": "Spy"}})

    def test_session_tracker_sessions_are_unique(self):
        tracker = SessionTracker(self.config)
        tracker.create_session()
        tracker.create_session()
        self.assertEqual(tracker.delivery_queue.qsize(), 2)
        session_one = tracker.delivery_queue.get(False)
        session_two = tracker.delivery_queue.get(False)
        self.assertNotEqual(session_one['id'], session_two['id'])

    def test_session_tracker_send_sessions_sends_sessions(self):
        client = Client(
            track_sessions=True,
            session_endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.create_session()
        self.assertEqual(client.session_tracker.delivery_queue.qsize(), 1)
        client.session_tracker.send_sessions()
        self.assertEqual(client.session_tracker.delivery_queue.qsize(), 0)
        json_body = self.server.received[0]['json_body']
        self.assertTrue('app' in json_body)
        self.assertTrue('notifier' in json_body)
        self.assertTrue('device' in json_body)
        self.assertTrue('sessions' in json_body)
        self.assertEqual(len(json_body['sessions']), 1)

    def test_session_tracker_sets_details_from_config(self):
        client = Client(
            track_sessions=True,
            session_endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.create_session()
        client.session_tracker.send_sessions()
        json_body = self.server.received[0]['json_body']
        # Notifier properties
        notifier = json_body['notifier']
        self.assertTrue('name' in notifier)
        self.assertEqual(notifier['name'], Notification.NOTIFIER_NAME)
        self.assertTrue('url' in notifier)
        self.assertEqual(notifier['url'], Notification.NOTIFIER_URL)
        self.assertTrue('version' in notifier)
        notifier_version = package_version('bugsnag') or 'unknown'
        self.assertEqual(notifier['version'], notifier_version)
        # App properties
        app = json_body['app']
        self.assertTrue('releaseStage' in app)
        self.assertEqual(app['releaseStage'], client.configuration.get('release_stage'))
        self.assertTrue('version' in app)
        self.assertEqual(app['version'], client.configuration.get('app_version'))
        # Device properties
        device = json_body['device']
        self.assertTrue('hostname' in device)
        self.assertEqual(device['hostname'], client.configuration.get('hostname'))

    def test_session_tracker_sends_when_threshold_hit(self):
        client = Client(
            track_sessions=True,
            session_endpoint=self.server.url,
            asynchronous=False
        )
        for i in range(51):
            client.session_tracker.create_session()
        # Wait for asynchronous delivery to be trigger
        time.sleep(0.01)
        json_body = self.server.received[0]['json_body']
        self.assertTrue('sessions' in json_body)
        self.assertEqual(len(json_body['sessions']), 50)

    def test_session_middleware_attaches_session_to_notification(self):
        client = Client(
            track_sessions=True,
            session_endpoint=self.server.url,
            endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.create_session()
        client.notify(Exception("Test"))
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