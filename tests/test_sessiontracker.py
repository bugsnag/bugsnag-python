import logging
import platform

from bugsnag import Client
from bugsnag.configuration import Configuration
from bugsnag.notifier import _NOTIFIER_INFORMATION
from bugsnag.sessiontracker import SessionTracker
from tests.utils import IntegrationTest
from unittest.mock import Mock


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
            session_endpoint=self.server.url,
            asynchronous=False
        )
        client.session_tracker.start_session()

        assert len(client.session_tracker.session_counts) == 1

        client.session_tracker.send_sessions()

        assert len(client.session_tracker.session_counts) == 0

        json_body = self.server.received[0]['json_body']

        assert 'app' in json_body
        assert 'notifier' in json_body
        assert 'device' in json_body
        assert len(json_body['sessionCounts']) == 1

    def test_session_tracker_sets_details_from_config(self):
        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            auto_capture_sessions=True,
            session_endpoint=self.server.url,
            asynchronous=False
        )

        client.session_tracker.start_session()
        client.session_tracker.send_sessions()
        json_body = self.server.received[0]['json_body']

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
            session_endpoint=self.server.url + '/ignore',
            endpoint=self.server.url,
            asynchronous=False
        )

        client.session_tracker.start_session()
        client.notify(Exception("Test"))

        assert len(self.server.received) == 1

        json_body = self.server.received[0]['json_body']
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
            session_endpoint=self.server.url,
            asynchronous=False,
            logger=logger,
        )

        client.session_tracker.send_sessions()

        assert self.server.sent_report_count == 0

        logger.debug.assert_called_once_with(
            "No sessions to deliver"
        )

    def test_session_tracker_does_not_send_when_disabled(self):
        logger = Mock(logging.Logger)

        client = Client(
            api_key='a05afff2bd2ffaf0ab0f52715bbdcffd',
            session_endpoint=self.server.url,
            asynchronous=False,
            release_stage="dev",
            notify_release_stages=["prod"],
            logger=logger,
        )

        client.session_tracker.start_session()
        client.session_tracker.send_sessions()

        assert self.server.sent_report_count == 0

        logger.debug.assert_called_once_with(
            "Not delivering due to release_stages"
        )

    def test_session_tracker_does_not_send_when_misconfigured(self):
        logger = Mock(logging.Logger)

        client = Client(
            api_key='',
            session_endpoint=self.server.url,
            asynchronous=False,
            logger=logger,
        )

        client.session_tracker.start_session()
        client.session_tracker.send_sessions()

        assert self.server.sent_report_count == 0

        logger.debug.assert_called_once_with(
            "Not delivering due to an invalid api_key"
        )
