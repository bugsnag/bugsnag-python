import sys

from bugsnag import Client, Configuration
from tests.utils import IntegrationTest, ScaryException


class ClientTest(IntegrationTest):
    def setUp(self):
        super(ClientTest, self).setUp()

        self.client = Client(api_key='testing client key',
                             use_ssl=False, endpoint=self.server.address,
                             asynchronous=False,
                             install_sys_hook=False)

    # Initialisation

    def test_init_no_configuration(self):
        client = Client(install_sys_hook=False)
        self.assertTrue(isinstance(client.configuration, Configuration))

    def test_init_configuration(self):
        configuration = Configuration()
        client = Client(configuration=configuration, install_sys_hook=False)

        self.assertEqual(client.configuration, configuration)

    def test_init_options(self):
        client = Client(api_key='testing client key', install_sys_hook=False)
        self.assertEqual(client.configuration.api_key, 'testing client key')

    # Sending Notification

    def test_notify_exception(self):
        self.client.notify(Exception('Testing Notify'))

        self.assertEqual(len(self.server.received), 1)

    def test_notify_exc_info(self):
        try:
            raise Exception('Testing Notify EXC Info')
        except Exception:
            self.client.notify_exc_info(*sys.exc_info())

        self.assertEqual(len(self.server.received), 1)

    def test_delivery(self):
        c = Configuration()
        self.called = False

        class FooDelivery:

            def deliver(foo, config, payload):
                self.called = True

        c.configure(delivery=FooDelivery(), api_key='abc')
        client = Client(c)
        client.notify(Exception('Oh no'))
        self.assertTrue(self.called)
        self.assertSentReportCount(0)
        del self.called

    def test_invalid_delivery(self):
        c = Configuration()
        c.configure(delivery=44, api_key='abc')
        client = Client(c)
        client.notify(Exception('Oh no'))

    def test_failed_delivery(self):
        c = Configuration()
        self.called = False

        class FooDelivery:

            def deliver(foo, config, payload):
                self.called = True
                raise ScaryException('something gone wrong')

        c.configure(delivery=FooDelivery(), api_key='abc')
        client = Client(c)
        client.notify(Exception('Oh no'))
        self.assertTrue(self.called)
        del self.called

    # Capture

    def test_notify_capture(self):
        try:
            with self.client.capture():
                raise Exception('Testing Notify Context')
        except Exception:
            pass

        self.assertEqual(len(self.server.received), 1)

    def test_notify_capture_raises(self):

        def foo():
            with self.client.capture():
                raise Exception('Testing Notify Context')

        self.assertRaises(Exception, foo)
        self.assertEqual(len(self.server.received), 1)

    def test_notify_capture_options(self):
        try:
            with self.client.capture(section={'key': 'value'}):
                raise Exception('Testing Notify Context')
        except Exception:
            pass

        self.assertEqual(len(self.server.received), 1)
        json_body = self.server.received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(event['metaData']['section'], {
            'key': 'value'
        })

    def test_notify_capture_change_severity(self):
        try:
            with self.client.capture(severity='info'):
                raise Exception('Testing Notify Context')
        except Exception:
            pass

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]

        self.assertEqual(event['severity'], "info")
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            "type": "userContextSetSeverity"
        })

    def test_notify_capture_types(self):
        try:
            with self.client.capture((ScaryException,)):
                raise Exception('Testing Notify Capture Types')
        except Exception:
            pass

        self.assertSentReportCount(0)

        try:
            with self.client.capture((ScaryException,)):
                raise ScaryException('Testing Notify Capture Types')
        except Exception:
            pass

        self.assertSentReportCount(1)
        self.assertExceptionName(0, 0, 'tests.utils.ScaryException')

    def test_no_exception_capture(self):
        with self.client.capture():
            pass

        self.assertEqual(len(self.server.received), 0)

    def test_capture_decorator(self):

        @self.client.capture
        def foo():
            raise Exception('Testing Capture Function')

        try:
            foo()
        except Exception:
            pass

        self.assertSentReportCount(1)

    def test_capture_decorator_mismatch(self):

        @self.client.capture
        def foo():
            pass

        self.assertRaises(TypeError, foo, 'bar')
        self.assertSentReportCount(1)

        payload = self.server.received[0]['json_body']
        file = payload['events'][0]['exceptions'][0]['stacktrace'][0]['file']

        self.assertEqual(file, "test_client.py")

    def test_capture_decorator_returns_value(self):

        @self.client.capture
        def foo():
            return "300"

        self.assertEqual(foo(), "300")

    def test_capture_decorator_change_severity(self):
        @self.client.capture(severity='info')
        def foo():
            raise Exception('Testing Capture Function')

        try:
            foo(Exception)
        except Exception:
            pass

        payload = self.server.received[0]['json_body']
        event = payload['events'][0]

        self.assertEqual(event['severity'], "info")
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            "type": "userContextSetSeverity"
        })

    def test_capture_decorator_raises(self):

        @self.client.capture
        def foo():
            raise Exception('Testing Capture Function')

        self.assertRaises(Exception, foo)

        self.assertSentReportCount(1)

    def test_capture_decorator_with_types(self):

        @self.client.capture((ScaryException,))
        def foo(exception_type):
            raise exception_type('Testing Capture Function with Types')

        try:
            foo(Exception)
        except Exception:
            pass

        self.assertSentReportCount(0)

        try:
            foo(ScaryException)
        except Exception:
            pass

        self.assertSentReportCount(1)

    def test_capture_decorator_with_class_method(self):
        class Test(object):
            @self.client.capture()
            def foo(self):
                raise Exception()

        try:
            test = Test()
            test.foo()
        except Exception:
            pass

        self.assertSentReportCount(1)

    # Exception Hook

    def test_exception_hook(self):
        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            self.client.excepthook(*sys.exc_info())

        self.assertEqual(len(self.server.received), 1)
        event = self.server.received[0]['json_body']['events'][0]
        self.assertEqual(event['severity'], 'error')

    def test_exception_hook_disabled(self):
        self.client.configuration.auto_notify = False

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            self.client.excepthook(*sys.exc_info())

        self.assertEqual(len(self.server.received), 0)

    def test_installed_except_hook(self):
        client = Client()

        # Prevent the existing hook from being called
        client.sys_excepthook = None

        self.hooked = None

        def hooked_except_hook(*exc_info):
            self.hooked = exc_info

        client.excepthook = hooked_except_hook

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            sys.excepthook(*sys.exc_info())

        self.assertEqual(self.hooked[0], Exception)

    def test_installed_except_hook_calls_previous_except_hook(self):
        self.hook_ran = False

        def excepthook(*exc_info):
            self.hook_ran = True
        sys.excepthook = excepthook

        client = Client(auto_notify=False)  # noqa

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            sys.excepthook(*sys.exc_info())

        self.assertTrue(self.hook_ran)

    def test_unregister_installed_except_hook(self):
        # Setup an original except hook
        def excepthook(*exc_info):
            pass
        sys.excepthook = excepthook

        client = Client()
        self.assertNotEqual(sys.excepthook, excepthook)
        client.uninstall_sys_hook()
        self.assertEqual(sys.excepthook, excepthook)

    # Multiple Clients

    def test_multiple_clients_different_keys(self):
        client1 = Client(api_key='abc', asynchronous=False, use_ssl=False,
                         endpoint=self.server.address)
        client2 = Client(api_key='456', asynchronous=False, use_ssl=False,
                         endpoint=self.server.address)

        client1.notify(ScaryException('foo'))
        self.assertSentReportCount(1)

        headers = self.server.received[0]['headers']

        client2.notify(ScaryException('bar'))
        self.assertSentReportCount(2)

        headers = self.server.received[1]['headers']
        self.assertEqual(headers['Bugsnag-Api-Key'], '456')

    def test_multiple_clients_one_excepthook(self):
        def excepthook(*exc_info):
            pass
        sys.excepthook = excepthook

        client1 = Client(api_key='abc', asynchronous=False, use_ssl=False,
                         endpoint=self.server.address)
        Client(api_key='456', asynchronous=False, use_ssl=False,
               endpoint=self.server.address, install_sys_hook=False)

        self.assertEqual(client1, sys.excepthook.bugsnag_client)
        self.assertEqual(client1.sys_excepthook, excepthook)

    # Session Tracking

    def test_session_tracker_object_exists(self):
        client = Client()
        self.assertTrue(hasattr(client, 'session_tracker'))
