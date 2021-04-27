import unittest
import threading

from bugsnag.sessiontracker import SessionTracker, SessionMiddleware
from bugsnag.configuration import Configuration
from bugsnag.event import Event


class TestSessionMiddleware(unittest.TestCase):
    def setUp(self):
        self.config = Configuration()
        self.config.configure(api_key='fff', auto_capture_sessions=False)
        self.sessiontracker = SessionTracker(self.config)
        self.sessiontracker.auto_sessions = True  # Stub session delivery queue

    def tearDown(self):
        pass

    def test_increment_counts(self):
        """
        Every event should keep a list of prior events which occurred in the
        session
        """

        def next_callable(event):
            pass

        middleware = SessionMiddleware(next_callable)
        self.sessiontracker.start_session()

        event = Event(Exception('shucks'), self.config, None)
        middleware(event)

        assert event.session['events']['unhandled'] == 0
        assert event.session['events']['handled'] == 1

        event2 = Event(Exception('oh no'), self.config, None)
        middleware(event2)

        assert event2.session['events']['unhandled'] == 0
        assert event2.session['events']['handled'] == 2

        # Session counts should not change for events already handled
        assert event.session['events']['unhandled'] == 0
        assert event.session['events']['handled'] == 1

    def test_it_does_nothing_if_no_session_exists(self):
        def run_session_middleware():
            def next_callable(event):
                pass

            try:
                thread.exc_info = None
                middleware = SessionMiddleware(next_callable)

                event = Event(Exception('shucks'), self.config, None)
                middleware(event)

                assert event.session is None
            except Exception:
                import sys
                thread.exc_info = sys.exc_info()

        thread = threading.Thread(target=run_session_middleware)
        thread.start()
        thread.join()

        # ensure there was no exception in the thread
        self.assertEqual(None, thread.exc_info, thread.exc_info)
