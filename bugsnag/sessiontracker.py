from __future__ import print_function
from uuid import uuid4
from time import strftime, gmtime
from threading import Lock, Timer
import atexit

import bugsnag
from bugsnag.utils import package_version, ThreadLocals, \
    FilterDict, SanitizingJSONEncoder
from bugsnag.notification import Notification


class SessionTracker(object):

    MAXIMUM_SESSION_COUNT = 100
    SESSION_PAYLOAD_VERSION = "1.0"

    """
    Session tracking class for Bugsnag
    """
    def __init__(self, configuration):
        self.session_counts = {}
        self.config = configuration
        self.mutex = Lock()
        self.auto_sessions = False
        self.delivery_thread = None

    def start_session(self):
        if not self.auto_sessions and self.config.auto_capture_sessions:
            self.auto_sessions = True
            self.__start_delivery()
        start_time = strftime('%Y-%m-%dT%H:%M:00', gmtime())
        new_session = {
            'id': uuid4().hex,
            'startedAt': start_time,
            'events': {
                'handled': 0,
                'unhandled': 0
            }
        }
        tls = ThreadLocals.get_instance()
        tls.set_item("bugsnag-session", new_session)
        self.__queue_session(start_time)

    def send_sessions(self):
        self.mutex.acquire()
        try:
            sessions = []
            for min_time, count in self.session_counts.items():
                sessions.append({
                    'startedAt': min_time,
                    'sessionsStarted': count
                })
            self.session_counts = {}
        finally:
            self.mutex.release()
        self.__deliver(sessions)

    def __start_delivery(self):
        if self.delivery_thread is None:
            def deliver():
                self.send_sessions()
                self.delivery_thread = Timer(30.0, deliver)
                self.delivery_thread.daemon = True
                self.delivery_thread.start()

            self.delivery_thread = Timer(30.0, deliver)
            self.delivery_thread.daemon = True
            self.delivery_thread.start()

            def cleanup():
                if self.delivery_thread is not None:
                    self.delivery_thread.cancel()
                self.send_sessions()

            atexit.register(cleanup)

    def __queue_session(self, start_time):
        self.mutex.acquire()
        try:
            if start_time not in self.session_counts:
                self.session_counts[start_time] = 0
            self.session_counts[start_time] += 1
        finally:
            self.mutex.release()

    def __deliver(self, sessions):
        if not sessions:
            bugsnag.logger.debug("No sessions to deliver")
            return

        if not self.config.api_key:
            bugsnag.logger.debug("Not delivering due to an invalid api_key")
            return

        if not self.config.should_notify:
            bugsnag.logger.debug("Not delivering due to release_stages")
            return

        notifier_version = package_version('bugsnag') or 'unknown'

        payload = {
            'notifier': {
                'name': Notification.NOTIFIER_NAME,
                'url': Notification.NOTIFIER_URL,
                'version': notifier_version
            },
            'device': FilterDict({
                'hostname': self.config.get('hostname'),
            }),
            'app': {
                'releaseStage': self.config.get('release_stage'),
                'version': self.config.get('app_version')
            },
            'sessionCounts': sessions
        }

        try:
            filters = self.config.params_filters
            encoder = SanitizingJSONEncoder(separators=(',', ':'),
                                            keyword_filters=filters)
            encoded_payload = encoder.encode(payload)
            self.config.delivery.deliver_sessions(self.config, encoded_payload)
        except Exception as e:
            bugsnag.logger.exception('Sending sessions failed %s', e)


class SessionMiddleware(object):
    """
    Session middleware ensures that a session is appended to the notification.
    """
    def __init__(self, bugsnag):
        self.bugsnag = bugsnag

    def __call__(self, notification):
        tls = ThreadLocals.get_instance()
        session = tls.get_item('bugsnag-session', {}).copy()
        if session:
            if notification.unhandled:
                session['events']['unhandled'] += 1
            else:
                session['events']['handled'] += 1
            notification.session = session
        self.bugsnag(notification)
