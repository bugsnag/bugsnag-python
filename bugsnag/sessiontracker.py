from __future__ import print_function
from uuid import uuid4
from time import strftime, gmtime, time
from threading import Lock, Thread

import bugsnag
from bugsnag.utils import SanitizingJSONEncoder, package_version,\
    ThreadLocals
from bugsnag.notification import Notification

try:
    from Queue import Queue
except ImportError:
    from queue import Queue


class SessionTracker(object):

    TIME_THRESHOLD = 60
    SESSION_PAYLOAD_VERSION = "1.0"

    """
    Session tracking class for Bugsnag
    """
    def __init__(self, configuration):
        self.user_callback = None
        self.delivery_queue = Queue()
        self.config = configuration
        self.mutex = Lock()
        self.lastsent = time()

    def set_user_callback(self, usercallback):
        self.user_callback = usercallback

    def create_session(self, user=None):
        if not self.config.track_sessions:
            return
        if not user:
            if callable(self.user_callback):
                user = self.user_callback()
            else:
                user = {}
                request_config = bugsnag.RequestConfiguration.get_instance()
                user.update(request_config.user)
                if request_config.user_id:
                    user['id'] = request_config.user_id
        new_session = {
            'id': uuid4().hex,
            'startedAt': strftime('%y-%m-%dT%H:%M:%S', gmtime())
        }
        session_copy = new_session.copy()
        session_copy.update({'user': user})
        if self.config.asynchronous:
            add_thread = Thread(target=self.__queue_session,
                                args=(session_copy,))
            add_thread.start()
        else:
            self.__queue_session(session_copy)
        new_session['events'] = {
            'handled': 0,
            'unhandled': 0
        }
        tls = ThreadLocals.get_instance()
        tls.set_item("bugsnag-session", new_session)

    def send_sessions(self):
        self.mutex.acquire()
        try:
            if self.config.asynchronous:
                deliver_thread = Thread(target=self.__deliver_sessions)
                deliver_thread.start()
            else:
                self.__deliver_sessions()
        finally:
            self.mutex.release()

    def __queue_session(self, session):
        self.mutex.acquire()
        try:
            if time() - self.lastsent > self.TIME_THRESHOLD:
                self.__deliver_sessions()
            self.delivery_queue.put(session)
        finally:
            self.mutex.release()

    def __deliver_sessions(self):
        if not self.config.track_sessions:
            return
        sessions = []
        while not self.delivery_queue.empty():
            sessions.append(self.delivery_queue.get())
        self.__deliver(sessions)

    def __deliver(self, sessions):
        if not sessions or not self.config.should_notify():
            return

        notifier_version = package_version('bugsnag') or 'unknown'

        filters = self.config.params_filters
        encoder = SanitizingJSONEncoder(separators=(',', ':'),
                                        keyword_filters=filters)
        payload = encoder.encode({
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
            'sessions': sessions
        })
        headers = {
            'Bugsnag-Api-Key': self.config.get('api_key'),
            'Bugsnag-Sent-At': strftime('%y-%m-%dT%H:%M:%S', gmtime()),
            'Bugsnag-Payload-Version': self.SESSION_PAYLOAD_VERSION
        }
        try:
            self.config.delivery.deliver(self.config,
                                         payload,
                                         self.config.session_endpoint,
                                         headers,
                                         True)
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
