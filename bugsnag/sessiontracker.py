from __future__ import print_function
from uuid import uuid4
from time import strftime, gmtime, time
from threading import Lock, Thread, Timer
from json import JSONEncoder

import bugsnag
from bugsnag.utils import package_version,\
    ThreadLocals
from bugsnag.notification import Notification

try:
    from Queue import Queue
except ImportError:
    from queue import Queue


class SessionTracker(object):

    TIME_THRESHOLD = 60
    FALLBACK_TIME = 300
    MAXIMUM_SESSION_COUNT = 50
    SESSION_PAYLOAD_VERSION = "1.0"

    """
    Session tracking class for Bugsnag
    """
    def __init__(self, configuration):
        self.session_counts = {}
        self.config = configuration
        self.mutex = Lock()
        self.lastsent = time()
        self.fallbacktimeout = None

    def create_session(self):
        if not self.config.track_sessions:
            return
        start_time = strftime('%Y-%m-%dT%H:%M:00', gmtime())
        new_session = {
            'id': uuid4().hex,
            'startedAt': start_time,
            'events': {
                'handled': 0,
                'unhandled': 0
            }
        }
        add_thread = Thread(target=self.__queue_session, args=(start_time,))
        add_thread.start()
        tls = ThreadLocals.get_instance()
        tls.set_item("bugsnag-session", new_session)

    def send_sessions(self):
        self.mutex.acquire()
        try:
            self.__deliver_sessions()
        finally:
            self.mutex.release()

    def __queue_session(self, start_time):
        self.mutex.acquire()
        try:
            if start_time not in self.session_counts:
                self.session_counts[start_time] = 0
            self.session_counts[start_time] += 1
            if time() - self.lastsent > self.TIME_THRESHOLD:
                self.__deliver_sessions()
        finally:
            self.mutex.release()

    def __reset_fallback_timer(self):
        if self.fallbacktimeout:
            self.fallbacktimeout.cancel()
        self.fallbacktimeout = Timer(self.FALLBACK_TIME, self.send_sessions)

    def __deliver_sessions(self):
        if not self.config.track_sessions:
            return
        sessions = []
        for min_time, count in self.session_counts.items():
            sessions.append({
                'startedAt': min_time,
                'sessionsStarted': count
            })
            if len(sessions) > self.MAXIMUM_SESSION_COUNT:
                self.__deliver(sessions)
                sessions = []
        self.session_counts = {}
        self.__reset_fallback_timer()
        self.__deliver(sessions)

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

        if not self.config.asynchronous:
            bugsnag.logger.debug("Delivering sessions requires async delivery")
            return

        notifier_version = package_version('bugsnag') or 'unknown'

        payload = {
            'notifier': {
                'name': Notification.NOTIFIER_NAME,
                'url': Notification.NOTIFIER_URL,
                'version': notifier_version
            },
            'device': {
                'hostname': self.config.get('hostname'),
            },
            'app': {
                'releaseStage': self.config.get('release_stage'),
                'version': self.config.get('app_version')
            },
            'sessionCounts': sessions
        }

        headers = {
            'Bugsnag-Api-Key': self.config.get('api_key'),
            'Bugsnag-Payload-Version': self.SESSION_PAYLOAD_VERSION
        }

        options = {
            'endpoint': self.config.session_endpoint,
            'headers': headers,
            'backoff': True,
            'success': 202
        }

        try:
            self.config.delivery.deliver(self.config, payload, options)
        except Exception as e:
            bugsnag.logger.exception('Sending sessions failed %s', e)
        self.lastsent = time()


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
