from __future__ import print_function
from uuid import uuid4
from time import strftime, gmtime
from threading import Lock, Thread

import bugsnag
from bugsnag.utils import SanitizingJSONEncoder, FilterDict, package_version,\
    ThreadLocals
from bugsnag.notification import Notification

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

class SessionTracker(object):

    MAX_PAYLOAD_SIZE = 50
    SESSION_PAYLOAD_VERSION = "1.0"

    """
    Session tracking class for Bugsnag
    """
    def __init__(self, configuration):
        self.usercallback = None
        self.deliveryqueue = Queue(self.MAX_PAYLOAD_SIZE)
        self.config = configuration
        self.mutex = Lock()
        self.lastsent = 0

    def setusercallback(self, usercallback):
        self.usercallback = usercallback

    def createsession(self, user=None):
        if not self.config.tracksessions:
            return
        if not user:
            if callable(self.usercallback):
                user = self.usercallback()
            else:
                user = {}
                requestconfig = bugsnag.RequestConfiguration.get_instance()
                user.update(requestconfig.user)
                if requestconfig.user_id:
                    user['id'] = requestconfig.user_id
        newsession = {
            'id': uuid4().hex,
            'startedAt': strftime('%y-%m-%dT%H:%M:%S', gmtime())
        }
        sessioncopy = newsession.copy()
        sessioncopy.update({'user': user})
        addthread = Thread(target=self.__queuesession, args=(sessioncopy,))
        addthread.start()
        newsession['events'] = {
            'handled': 0,
            'unhandled': 0
        }
        tls = ThreadLocals.get_instance()
        tls.setitem("bugsnag-session", newsession)

    def sendsessions(self):
        self.mutex.acquire()
        try:
            self.__deliversessions()
        finally:
            self.mutex.release()

    def __queuesession(self, session):
        self.mutex.acquire()
        try:
            if self.deliveryqueue.full():
                self.__deliversessions()
            self.deliveryqueue.put(session)
        finally:
            self.mutex.release()

    def __deliversessions(self):
        if not self.config.tracksessions:
            return
        sessions = []
        while not self.deliveryqueue.empty():
            sessions.append(self.deliveryqueue.get())
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
            self.config.delivery.deliver(self.config, payload, \
                self.config.sessionendpoint, headers)
        except Exception as e:
            bugsnag.logger.exception('Notifying Bugsnag failed %s', e)


class SessionMiddleware(object):
    """
    Session middleware ensures that a session is appended to the notification.
    """
    def __init__(self, bugsnag):
        
        self.bugsnag = bugsnag

    def __call__(self, notification):
        tls = ThreadLocals.get_instance()
        session = tls.getitem('bugsnag-session', {}).copy()
        if session:
            if notification.unhandled:
                session['events']['unhandled'] += 1
            else:
                session['events']['handled'] += 1
            notification.session = session
            
        self.bugsnag(notification)
