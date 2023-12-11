import logging
import platform

from bugsnag import Client
from bugsnag.configuration import Configuration
from bugsnag.notifier import _NOTIFIER_INFORMATION
from bugsnag.sessiontracker import SessionTracker
from tests.utils import IntegrationTest
from unittest.mock import Mock


def force_timer_to_fire(timer):
    assert timer is not None

    # setting and clearing the 'finished' Event forces the timer to fire
    # immediately:
    # https://github.com/python/cpython/blob/ca11aec98c39a08da858a1270b13b7e3ae6aa53b/Lib/threading.py#L1415-L1419
    timer.finished.set()
    timer.finished.clear()


class TestConfiguration(IntegrationTest):
    def test_session_tracker_adds_session_object_to_queue(self):
        config = Configuration()
        config.auto_capture_sessions = True

        tracker = SessionTracker(config)
        tracker.auto_sessions = True
        tracker.start_session()

        assert len(tracker.session_counts) == 1

        for key, value in tracker.session_counts.items():
            assert value == 1

    def test_session_tracker_send_sessions_sends_sessions(self):
        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            auto_capture_sessions=True,
            session_endpoint=self.server.sessions_url,
            asynchronous=False
        )
        client.session_tracker.start_session()

        assert len(client.session_tracker.session_counts) == 1

        client.session_tracker.send_sessions()

        assert len(client.session_tracker.session_counts) == 0

        json_body = self.server.sessions_received[0]['json_body']

        assert 'app' in json_body
        assert 'notifier' in json_body
        assert 'device' in json_body
        assert len(json_body['sessionCounts']) == 1

    def test_session_tracker_sets_details_from_config(self):
        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            auto_capture_sessions=True,
            session_endpoint=self.server.sessions_url,
            asynchronous=False
        )

        client.session_tracker.start_session()
        client.session_tracker.send_sessions()
        json_body = self.server.sessions_received[0]['json_body']

        # Notifier properties
        assert json_body['notifier'] == _NOTIFIER_INFORMATION

        # App properties
        app = json_body['app']
        assert app['releaseStage'] == client.configuration.release_stage
        assert app['version'] == client.configuration.app_version

        # Device properties
        device = json_body['device']
        assert device['hostname'] == client.configuration.hostname
        assert device['runtimeVersions']['python'] == platform.python_version()

    def test_session_middleware_attaches_session_to_event(self):
        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            session_endpoint='http://' + self.server.address + '/ignore',
            endpoint=self.server.events_url,
            asynchronous=False
        )

        client.session_tracker.start_session()
        client.notify(Exception("Test"))

        assert len(self.server.events_received) == 1

        json_body = self.server.events_received[0]['json_body']
        session = json_body['events'][0]['session']

        assert 'id' in session
        assert 'startedAt' in session
        assert session['events'] == {
            'unhandled': 0,
            'handled': 1,
        }

    def test_session_tracker_does_not_send_when_nothing_to_send(self):
        logger = Mock(logging.Logger)

        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            session_endpoint=self.server.sessions_url,
            asynchronous=False,
            logger=logger,
        )

        client.session_tracker.send_sessions()

        assert self.server.sent_session_count == 0

        logger.debug.assert_called_once_with(
            "No sessions to deliver"
        )

    def test_session_tracker_does_not_send_when_disabled(self):
        logger = Mock(logging.Logger)

        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            session_endpoint=self.server.sessions_url,
            asynchronous=False,
            release_stage="dev",
            notify_release_stages=["prod"],
            logger=logger,
        )

        client.session_tracker.start_session()
        client.session_tracker.send_sessions()

        assert self.server.sent_session_count == 0

        logger.debug.assert_called_once_with(
            "Not delivering due to release_stages"
        )

    def test_session_tracker_does_not_send_when_misconfigured(self):
        logger = Mock(logging.Logger)

        client = Client(
            api_key='',
            session_endpoint=self.server.sessions_url,
            asynchronous=False,
            logger=logger,
        )

        client.session_tracker.start_session()
        client.session_tracker.send_sessions()

        assert self.server.sent_session_count == 0

        logger.debug.assert_called_once_with(
            "Not delivering due to an invalid api_key"
        )

    def test_session_tracker_starts_delivery_when_auto_capture_is_on(self):
        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            auto_capture_sessions=True,
            session_endpoint=self.server.sessions_url,
            asynchronous=False
        )

        client.session_tracker.start_session()

        force_timer_to_fire(client.session_tracker.delivery_thread)

        self.server.wait_for_session()

        assert self.server.sent_session_count == 1

    def test_session_tracker_starts_delivery_when_auto_capture_is_off(self):
        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            auto_capture_sessions=False,
            session_endpoint=self.server.sessions_url,
            asynchronous=False
        )

        client.session_tracker.start_session()

        force_timer_to_fire(client.session_tracker.delivery_thread)

        self.server.wait_for_session()

        assert self.server.sent_session_count == 1
