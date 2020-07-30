import bugsnag
import threading


class Terrible(Exception):
    pass


def test_uncaught_exception_on_thread_sends_event(bugsnag_server):
    """
    Python 3.8+ has an excepthook for spawned threads. This test checks that
    exceptions thrown by threads are handled.
    """

    def process():
        raise Terrible('oh no')

    def my_program(*args):
        return process()

    def callback(event):
        event.severity = "info"

    bugsnag.configure(app_type='dispatch')
    bugsnag.before_notify(callback)
    thread = threading.Thread(target=my_program)
    thread.start()
    thread.join()

    bugsnag_server.wait_for_request()

    event = bugsnag_server.received[0]['json_body']['events'][0]
    exception = event['exceptions'][0]

    assert 'dispatch' == event['app']['type']
    assert 'info' == event['severity']
    assert 'test_thread_excepthook.Terrible' == exception['errorClass']
    assert 'oh no' == exception['message']
    assert 'process' == exception['stacktrace'][0]['method']
    assert exception['stacktrace'][0]['inProject']
    assert 'my_program' == exception['stacktrace'][1]['method']
    assert exception['stacktrace'][1]['inProject']
    assert not exception['stacktrace'][2]['inProject']
