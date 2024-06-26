from copy import deepcopy
from uuid import uuid4
from time import strftime, gmtime
from threading import Lock, Timer
from typing import List, Dict, Callable
import atexit

try:
    from contextvars import ContextVar
    _session_info = ContextVar('bugsnag-session', default={})  # type: ignore
except ImportError:
    from bugsnag.utils import ThreadContextVar
    # flake8: noqa
    _session_info = ThreadContextVar('bugsnag-session', default={})  # type: ignore

from bugsnag.notifier import _NOTIFIER_INFORMATION
from bugsnag.utils import FilterDict, SanitizingJSONEncoder
from bugsnag.event import Event
from bugsnag.request_tracker import RequestTracker


__all__ = []  # type: List[str]


class SessionTracker:

    MAXIMUM_SESSION_COUNT = 100
    SESSION_PAYLOAD_VERSION = "1.0"

    """
    Session tracking class for Bugsnag
    """

    def __init__(self, configuration):
        self.session_counts = {}  # type: Dict[str, int]
        self.config = configuration
        self.mutex = Lock()
        self.auto_sessions = False
        self.delivery_thread = None
        self._request_tracker = RequestTracker()

    def start_session(self):
        if not self.auto_sessions:
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
        _session_info.set(new_session)
        self.__queue_session(start_time)

    def send_sessions(self, asynchronous=True):
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

        self.__deliver(sessions, asynchronous)

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

                self.send_sessions(asynchronous=False)

            atexit.register(cleanup)

    def __queue_session(self, start_time: str):
        self.mutex.acquire()
        try:
            if start_time not in self.session_counts:
                self.session_counts[start_time] = 0
            self.session_counts[start_time] += 1
        finally:
            self.mutex.release()

    def __deliver(self, sessions: List[Dict], asynchronous=True):
        if not sessions:
            self.config.logger.debug("No sessions to deliver")
            return

        if not self.config.api_key:
            self.config.logger.debug(
                "Not delivering due to an invalid api_key"
            )
            return

        if not self.config.should_notify():
            self.config.logger.debug("Not delivering due to release_stages")
            return

        payload = {
            'notifier': _NOTIFIER_INFORMATION,
            'device': FilterDict({
                'hostname': self.config.hostname,
                'runtimeVersions': self.config.runtime_versions
            }),
            'app': {
                'releaseStage': self.config.release_stage,
                'version': self.config.app_version
            },
            'sessionCounts': sessions
        }

        try:
            encoder = SanitizingJSONEncoder(
                self.config.logger,
                separators=(',', ':'),
                keyword_filters=self.config.params_filters
            )

            encoded_payload = encoder.encode(payload)

            deliver = self.config.delivery.deliver_sessions

            if (
                hasattr(deliver, '__code__') and
                'options' in deliver.__code__.co_varnames
            ):
                try:
                    post_delivery_callback = self._request_tracker.new_request()

                    deliver(
                        self.config,
                        encoded_payload,
                        options={
                            'asynchronous': asynchronous,
                            'post_delivery_callback': post_delivery_callback,
                        }
                    )
                except Exception:
                    # ensure the request is not still marked as pending
                    post_delivery_callback()
                    raise

            else:
                deliver(self.config, encoded_payload)

        except Exception as e:
            self.config.logger.exception('Sending sessions failed %s', e)


class SessionMiddleware:
    """
    Session middleware ensures that a session is appended to the event.
    """
    def __init__(self, bugsnag: Callable[[Event], Callable]):
        self.bugsnag = bugsnag

    def __call__(self, event: Event):
        session = _session_info.get()
        if session:
            if event.unhandled:
                session['events']['unhandled'] += 1
            else:
                session['events']['handled'] += 1
            event.session = deepcopy(session)
        self.bugsnag(event)
