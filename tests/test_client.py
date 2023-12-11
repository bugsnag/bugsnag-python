import os
import re
import sys
import pytest
import inspect
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, ANY
from tests import fixtures

from bugsnag import (
    Client,
    Configuration,
    BreadcrumbType,
    Breadcrumb,
    FeatureFlag
)

import bugsnag.legacy as legacy
from tests.utils import IntegrationTest, ScaryException

timestamp_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}(?:[+-]\d{2}:\d{2}|Z)'  # noqa: E501


def is_valid_timestamp(timestamp: str) -> bool:
    return bool(re.search(timestamp_regex, timestamp))


class ClientTest(IntegrationTest):
    def setUp(self):
        super(ClientTest, self).setUp()

        self.client = Client(
            api_key='testing client key',
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            project_root=os.path.join(os.getcwd(), 'tests'),
            asynchronous=False,
            install_sys_hook=False
        )

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

    # Sending Event

    def test_notify_exception(self):
        self.client.notify(Exception('Testing Notify'))

        self.assertEqual(len(self.server.events_received), 1)

    def test_notify_exc_info(self):
        try:
            raise Exception('Testing Notify EXC Info')
        except Exception:
            self.client.notify_exc_info(*sys.exc_info())

        self.assertEqual(len(self.server.events_received), 1)

    def test_delivery(self):
        c = Configuration()
        self.called = False

        class FooDelivery:

            def deliver(foo, config, payload, options={}):
                self.called = True

        c.configure(delivery=FooDelivery(), api_key='abc')
        client = Client(c)
        client.notify(Exception('Oh no'))
        self.assertTrue(self.called)
        self.assertSentReportCount(0)
        del self.called

    def test_invalid_delivery(self):
        c = Configuration()

        with pytest.warns(RuntimeWarning) as records:
            c.configure(delivery=44, api_key='abc')

            assert len(records) == 1
            assert str(records[0].message) == (
                'delivery should implement Delivery interface, got int. This '
                'will be an error in a future release.'
            )

        client = Client(c)
        client.notify(Exception('Oh no'))

    def test_failed_delivery(self):
        c = Configuration()
        self.called = False

        class FooDelivery:

            def deliver(foo, config, payload, options={}):
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

        self.assertEqual(len(self.server.events_received), 1)

    def test_notify_capture_raises(self):

        def foo():
            with self.client.capture():
                raise Exception('Testing Notify Context')

        self.assertRaises(Exception, foo)
        self.assertEqual(len(self.server.events_received), 1)

    def test_notify_capture_options(self):
        try:
            with self.client.capture(section={'key': 'value'}):
                raise Exception('Testing Notify Context')
        except Exception:
            pass

        self.assertEqual(len(self.server.events_received), 1)
        json_body = self.server.events_received[0]['json_body']
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

        payload = self.server.events_received[0]['json_body']
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

        self.assertEqual(len(self.server.events_received), 0)

    def test_capture_decorator(self):
        @self.client.capture
        def foo():
            raise Exception('Testing Capture Function')

        try:
            foo()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']

        assert len(stacktrace) == 2

        line = inspect.getsourcelines(foo)[1]

        assert stacktrace[0]['file'] == "test_client.py"
        assert stacktrace[0]['method'] == "foo"
        assert stacktrace[0]['inProject']

        # the first frame is the 'raise Exception(...)' line
        assert stacktrace[0]['lineNumber'] == line + 2

        assert stacktrace[1]['file'] == "test_client.py"
        assert stacktrace[1]['method'] == "foo"
        assert stacktrace[1]['inProject']

        # the second frame is the function 'foo' itself, which is added by our
        # capture decorator
        assert stacktrace[1]['lineNumber'] == line

    def test_capture_decorator_mismatch(self):
        @self.client.capture
        def foo():
            pass

        self.assertRaises(TypeError, foo, 'bar')
        self.assertSentReportCount(1)

        payload = self.server.events_received[0]['json_body']
        stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']

        assert len(stacktrace) == 1

        frame = stacktrace[0]

        assert frame['file'] == "test_client.py"
        assert frame['method'] == "foo"
        assert frame['inProject']
        assert frame['lineNumber'] == inspect.getsourcelines(foo)[1]

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

        payload = self.server.events_received[0]['json_body']
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

        self.assertEqual(len(self.server.events_received), 1)
        event = self.server.events_received[0]['json_body']['events'][0]
        self.assertEqual(event['severity'], 'error')

    def test_exception_hook_disabled(self):
        self.client.configuration.auto_notify = False

        try:
            raise Exception('Testing excepthook notify')
        except Exception:
            self.client.excepthook(*sys.exc_info())

        self.assertEqual(len(self.server.events_received), 0)

    def test_exception_hook_leaves_a_breadcrumb(self):
        assert len(self.server.events_received) == 0

        try:
            beep = boop  # noqa: F841, F821
        except Exception:
            self.client.excepthook(*sys.exc_info())

        assert len(self.server.events_received) == 1
        assert len(self.client.configuration.breadcrumbs) == 1

        breadcrumb = self.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'NameError'
        assert breadcrumb.metadata == {
            'errorClass': 'NameError',
            'message': "name 'boop' is not defined",
            'unhandled': True,
            'severity': 'error'
        }
        assert breadcrumb.type == BreadcrumbType.ERROR
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_exception_hook_does_not_leave_a_breadcrumb_if_errors_are_disabled(
        self
    ):
        # enable all type except 'ERROR'
        self.client.configuration.configure(
            enabled_breadcrumb_types=[
                BreadcrumbType.NAVIGATION,
                BreadcrumbType.REQUEST,
                BreadcrumbType.PROCESS,
                BreadcrumbType.LOG,
                BreadcrumbType.USER,
                BreadcrumbType.STATE,
                BreadcrumbType.MANUAL,
            ]
        )

        assert len(self.server.events_received) == 0

        try:
            beep = boop  # noqa: F841, F821
        except Exception:
            self.client.excepthook(*sys.exc_info())

        assert len(self.server.events_received) == 1
        assert len(self.client.configuration.breadcrumbs) == 0

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
        client1 = Client(
            api_key='abc',
            asynchronous=False,
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
        )
        client2 = Client(
            api_key='456',
            asynchronous=False,
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
        )

        client1.notify(ScaryException('foo'))
        self.assertSentReportCount(1)

        headers = self.server.events_received[0]['headers']

        client2.notify(ScaryException('bar'))
        self.assertSentReportCount(2)

        headers = self.server.events_received[1]['headers']
        self.assertEqual(headers['Bugsnag-Api-Key'], '456')

    def test_multiple_clients_one_excepthook(self):
        def excepthook(*exc_info):
            pass
        sys.excepthook = excepthook

        client1 = Client(
            api_key='456',
            asynchronous=False,
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
        )
        Client(
            api_key='456',
            asynchronous=False,
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            install_sys_hook=False,
        )

        self.assertEqual(client1, sys.excepthook.bugsnag_client)
        self.assertEqual(client1.sys_excepthook, excepthook)

    def test_session_tracker_object_exists(self):
        client = Client()
        self.assertTrue(hasattr(client, 'session_tracker'))

    def test_breadcrumbs_are_read_only(self):
        client = Client()
        assert client.breadcrumbs == []

        client.breadcrumbs.append('definitely a breadcrumb')
        assert client.breadcrumbs == []

        with pytest.raises(AttributeError) as e:
            client.breadcrumbs = ['??']

            assert str(e) == "AttributeError: can't set attribute"

    def test_on_breadcrumb_callbacks_can_be_added_and_removed(self):
        client = Client()
        config = client.configuration
        assert config._on_breadcrumbs == []

        def on_breadcrumb():
            pass

        on_breadcrumb_2 = lambda: None  # noqa: E731

        client.add_on_breadcrumb(on_breadcrumb)
        assert config._on_breadcrumbs == [on_breadcrumb]

        client.add_on_breadcrumb(on_breadcrumb_2)
        assert config._on_breadcrumbs == [on_breadcrumb, on_breadcrumb_2]

        client.remove_on_breadcrumb(on_breadcrumb)
        assert config._on_breadcrumbs == [on_breadcrumb_2]

        client.remove_on_breadcrumb(on_breadcrumb_2)
        assert config._on_breadcrumbs == []

    def test_removing_a_nonexistent_on_breadcrumb_callback_does_nothing(self):
        client = Client()

        client.remove_on_breadcrumb(lambda: None)
        assert client.configuration._on_breadcrumbs == []

    def test_legacy_on_breadcrumb_callbacks_can_be_added_and_removed(self):
        client = legacy.default_client
        config = client.configuration
        assert config._on_breadcrumbs == []

        def on_breadcrumb():
            pass

        on_breadcrumb_2 = lambda: None  # noqa: E731

        client.add_on_breadcrumb(on_breadcrumb)
        assert config._on_breadcrumbs == [on_breadcrumb]

        client.add_on_breadcrumb(on_breadcrumb_2)
        assert config._on_breadcrumbs == [on_breadcrumb, on_breadcrumb_2]

        client.remove_on_breadcrumb(on_breadcrumb)
        assert config._on_breadcrumbs == [on_breadcrumb_2]

        client.remove_on_breadcrumb(on_breadcrumb_2)
        assert config._on_breadcrumbs == []

    def test_legacy_leave_breadcrumb_defaults(self):
        client = legacy.default_client
        assert len(client.configuration.breadcrumbs) == 0

        legacy.leave_breadcrumb('abc')
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abc'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.MANUAL
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_legacy_leave_breadcrumb_with_metadata_and_type(self):
        client = legacy.default_client
        assert len(client.configuration.breadcrumbs) == 0

        legacy.leave_breadcrumb('xyz', {'a': 2}, BreadcrumbType.LOG)
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'xyz'
        assert breadcrumb.metadata == {'a': 2}
        assert breadcrumb.type == BreadcrumbType.LOG
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_leave_breadcrumb_defaults(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        client.leave_breadcrumb('abc')
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abc'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.MANUAL
        assert is_valid_timestamp(breadcrumb.timestamp)

    @pytest.mark.skipif(
        sys.version_info < (3, 7),
        reason="requires datetime.fromisoformat (Python 3.7 or higher)"
    )
    def test_leave_breadcrumb_timestamp_is_close_to_now(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        client.leave_breadcrumb('abc')
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abc'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.MANUAL
        assert is_valid_timestamp(breadcrumb.timestamp)

        now = datetime.now(timezone.utc)
        parsed_timestamp = datetime.fromisoformat(breadcrumb.timestamp)

        difference = now - parsed_timestamp
        assert difference < timedelta(seconds=5)

    def test_leave_breadcrumb_with_metadata_and_type(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        client.leave_breadcrumb('xyz', {'a': 2}, BreadcrumbType.LOG)
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'xyz'
        assert breadcrumb.metadata == {'a': 2}
        assert breadcrumb.type == BreadcrumbType.LOG
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_leave_breadcrumb_with_invalid_type(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        client.leave_breadcrumb('abcxyz', type='bad')
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abcxyz'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.MANUAL
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_leave_breadcrumb_does_nothing_when_max_breadcrumbs_is_0(self):
        client = Client()
        client.configuration.configure(max_breadcrumbs=0)
        assert len(client.configuration.breadcrumbs) == 0

        client.leave_breadcrumb('abc')
        assert len(client.configuration.breadcrumbs) == 0

    def test_leave_breadcrumb_passes_breadcrumb_to_callbacks(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        was_called = False

        def on_breadcrumb(breadcrumb):
            assert breadcrumb.message == 'oh no'
            assert breadcrumb.metadata == {'bad?': 'yes, very'}
            assert breadcrumb.type == BreadcrumbType.ERROR
            assert is_valid_timestamp(breadcrumb.timestamp)

            nonlocal was_called
            was_called = True

        client.add_on_breadcrumb(on_breadcrumb)

        client.leave_breadcrumb(
            'oh no',
            type=BreadcrumbType.ERROR,
            metadata={'bad?': 'yes, very'}
        )

        assert len(client.configuration.breadcrumbs) == 1
        assert was_called

    def test_breadcrumbs_are_mutable_in_on_breadcrumb_callbacks(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        def on_breadcrumb(breadcrumb):
            breadcrumb.message = 'abc'
            breadcrumb.type = BreadcrumbType.LOG
            breadcrumb.metadata = {'good?': 'extremely'}

        client.add_on_breadcrumb(on_breadcrumb)

        client.leave_breadcrumb(
            'oh no',
            type=BreadcrumbType.ERROR,
            metadata={'bad?': 'yes, very'}
        )

        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abc'
        assert breadcrumb.type == BreadcrumbType.LOG
        assert breadcrumb.metadata == {'good?': 'extremely'}
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_leave_breadcrumb_calls_on_breadcrumb_callbacks_in_order(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        calls = []

        client.add_on_breadcrumb(lambda x: calls.append(1))
        client.add_on_breadcrumb(lambda x: calls.append(2))
        client.add_on_breadcrumb(lambda x: calls.append(3))
        client.add_on_breadcrumb(lambda x: calls.append(4))

        client.leave_breadcrumb('abc')

        assert calls == [1, 2, 3, 4]

        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abc'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.MANUAL
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_leave_breadcrumb_stops_if_on_breadcrumb_callback_returns_false(self):  # noqa: E501
        logger = Mock(logging.Logger)

        client = Client()
        client.configuration.configure(logger=logger)
        assert len(client.configuration.breadcrumbs) == 0

        calls = []

        client.add_on_breadcrumb(lambda x: calls.append(1))
        client.add_on_breadcrumb(lambda x: calls.append(2))
        client.add_on_breadcrumb(lambda x: False)
        client.add_on_breadcrumb(lambda x: calls.append(3))

        client.leave_breadcrumb('abc')

        assert calls == [1, 2]
        assert len(client.configuration.breadcrumbs) == 0

        logger.info.assert_called_once_with(
            'Breadcrumb not attached due to on_breadcrumb callback'
        )

    def test_leave_breadcrumb_continues_if_on_breadcrumb_callback_raises(self):
        logger = Mock(logging.Logger)

        client = Client()
        client.configuration.configure(logger=logger)
        assert len(client.configuration.breadcrumbs) == 0

        def raises(breadcrumb):
            raise Exception('oh no')

        calls = []

        client.add_on_breadcrumb(lambda x: calls.append(1))
        client.add_on_breadcrumb(lambda x: calls.append(2))
        client.add_on_breadcrumb(raises)
        client.add_on_breadcrumb(lambda x: calls.append(3))

        client.leave_breadcrumb('xyz')

        assert calls == [1, 2, 3]
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'xyz'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.MANUAL
        assert is_valid_timestamp(breadcrumb.timestamp)

        logger.exception.assert_called_once_with(
            'Exception raised in on_breadcrumb callback'
        )

    def test_notify_with_breadcrumbs(self):
        assert len(self.server.events_received) == 0

        self.client.leave_breadcrumb('breadcrumb 1')
        self.client.leave_breadcrumb('breadcrumb 2', type=BreadcrumbType.USER)
        self.client.leave_breadcrumb('breadcrumb 3', metadata={'a': 1, 'b': 2})

        self.client.notify(Exception('hello'))

        assert len(self.server.events_received) == 1

        payload = self.server.events_received[0]['json_body']
        event = payload['events'][0]

        assert len(event['breadcrumbs']) == 3

        breadcrumbs = event['breadcrumbs']

        assert breadcrumbs[0]['name'] == 'breadcrumb 1'
        assert breadcrumbs[0]['metaData'] == {}
        assert breadcrumbs[0]['type'] == BreadcrumbType.MANUAL.value
        assert is_valid_timestamp(breadcrumbs[0]['timestamp'])

        assert breadcrumbs[1]['name'] == 'breadcrumb 2'
        assert breadcrumbs[1]['metaData'] == {}
        assert breadcrumbs[1]['type'] == BreadcrumbType.USER.value
        assert is_valid_timestamp(breadcrumbs[1]['timestamp'])

        assert breadcrumbs[2]['name'] == 'breadcrumb 3'
        assert breadcrumbs[2]['metaData'] == {'a': 1, 'b': 2}
        assert breadcrumbs[2]['type'] == BreadcrumbType.MANUAL.value
        assert is_valid_timestamp(breadcrumbs[2]['timestamp'])

    def test_handled_notify_leaves_a_new_breadcrumb(self):
        assert len(self.server.events_received) == 0

        self.client.notify(Exception('hello'))

        assert len(self.server.events_received) == 1
        assert len(self.client.configuration.breadcrumbs) == 1

        breadcrumb = self.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'Exception'
        assert breadcrumb.metadata == {
            'errorClass': 'Exception',
            'message': 'hello',
            'unhandled': False,
            'severity': 'warning'
        }
        assert breadcrumb.type == BreadcrumbType.ERROR
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_unhandled_notify_leaves_a_new_breadcrumb(self):
        assert len(self.server.events_received) == 0

        self.client.notify(
            IndexError('hello 123'),
            unhandled=True,
            severity='error'
        )

        assert len(self.server.events_received) == 1
        assert len(self.client.configuration.breadcrumbs) == 1

        breadcrumb = self.client.configuration.breadcrumbs[0]
        assert breadcrumb.message == 'IndexError'
        assert breadcrumb.metadata == {
            'errorClass': 'IndexError',
            'message': 'hello 123',
            'unhandled': True,
            'severity': 'error'
        }
        assert breadcrumb.type == BreadcrumbType.ERROR
        assert is_valid_timestamp(breadcrumb.timestamp)

    def test_notify_does_not_leave_a_breadcrumb_if_errors_are_disabled(self):
        # enable all type except 'ERROR'
        self.client.configuration.configure(
            enabled_breadcrumb_types=[
                BreadcrumbType.NAVIGATION,
                BreadcrumbType.REQUEST,
                BreadcrumbType.PROCESS,
                BreadcrumbType.LOG,
                BreadcrumbType.USER,
                BreadcrumbType.STATE,
                BreadcrumbType.MANUAL,
            ]
        )

        assert len(self.server.events_received) == 0

        self.client.notify(Exception('hello'))

        assert len(self.server.events_received) == 1
        assert len(self.client.configuration.breadcrumbs) == 0

    def test_can_modify_breadcrumbs_in_before_notify_callbacks(self):
        assert len(self.server.events_received) == 0

        self.client.leave_breadcrumb('a bad breadcrumb', metadata={'a': 1})

        def on_error(event):
            # these changes should take effect as breadcrumbs are mutable
            event.breadcrumbs[0].message = 'a good breadcrumb'
            event.breadcrumbs[0].metadata['a'] = 100
            event.breadcrumbs[0].type = BreadcrumbType.LOG

            # this change should not as the breadcrumb list is readonly
            event.breadcrumbs.append(
                Breadcrumb('haha', BreadcrumbType.LOG, {}, 'now')
            )

        self.client.configuration.middleware.before_notify(on_error)

        self.client.notify(Exception('hello'))

        assert len(self.server.events_received) == 1

        payload = self.server.events_received[0]['json_body']
        event = payload['events'][0]

        assert len(event['breadcrumbs']) == 1
        assert event['breadcrumbs'][0]['name'] == 'a good breadcrumb'
        assert event['breadcrumbs'][0]['metaData'] == {'a': 100}
        assert event['breadcrumbs'][0]['type'] == BreadcrumbType.LOG.value
        assert is_valid_timestamp(event['breadcrumbs'][0]['timestamp'])

        # changes in the on_error callback shouldn't apply to the client
        config = self.client.configuration
        assert config.breadcrumbs[0].message == 'a bad breadcrumb'
        assert config.breadcrumbs[0].metadata == {'a': 1}
        assert config.breadcrumbs[0].type == BreadcrumbType.MANUAL

    def test_synchronous_delivery_failures_are_logged(self):
        assert len(self.server.events_received) == 0

        logger = Mock(logging.Logger)

        self.client.configuration.logger = logger
        self.client.configuration.endpoint = 'https://localhost:4'

        self.client.notify(
            IndexError('hello 123'),
            unhandled=True,
            severity='error',
            asynchronous=False,
        )

        assert len(self.server.events_received) == 0

        logger.exception.assert_called_once_with(
            'Notifying Bugsnag failed %s',
            ANY
        )

    def test_asynchronous_delivery_failures_are_logged(self):
        assert len(self.server.events_received) == 0

        logger = Mock(logging.Logger)

        self.client.configuration.logger = logger
        self.client.configuration.endpoint = 'https://localhost:4'

        self.client.notify(
            IndexError('hello 123'),
            unhandled=True,
            severity='error',
            asynchronous=True,
        )

        assert len(self.server.events_received) == 0

        logger.exception.assert_called_once_with(
            'Notifying Bugsnag failed %s',
            ANY
        )

    def test_chained_exceptions_with_explicit_cause(self):
        self.client.notify(fixtures.exception_with_explicit_cause)

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 3

        assert exceptions[0]['message'] == 'a'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'
        assert exceptions[0]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 5,
                'method': 'raise_exception_with_explicit_cause',
                'inProject': True,
                'code': {
                    '2': '    try:',
                    '3': '        b()',
                    '4': '    except Exception as cause:',
                    '5': "        raise NameError('a') from cause",
                    '6': '',
                    '7': '',
                    '8': 'def b():'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 20,
                'method': '<module>',
                'inProject': True,
                'code': {
                    '17': '',
                    '18': '',
                    '19': 'try:',
                    '20': '    raise_exception_with_explicit_cause()',
                    '21': 'except Exception as exception:',
                    '22': '    exception_with_explicit_cause = exception',
                    '23': ''
                }
            }
        ]

        assert exceptions[1]['message'] == 'b'
        assert exceptions[1]['errorClass'] == 'ArithmeticError'
        assert exceptions[1]['type'] == 'python'
        assert exceptions[1]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 12,
                'method': 'b',
                'inProject': True,
                'code': {
                    '9': '    try:',
                    '10': '        c()',
                    '11': '    except Exception as cause:',
                    '12': '        raise ArithmeticError(\'b\') from cause',
                    '13': '',
                    '14': '',
                    '15': 'def c():'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 3,
                'method': 'raise_exception_with_explicit_cause',
                'inProject': True,
                'code': {
                    '1': 'def raise_exception_with_explicit_cause():',
                    '2': '    try:',
                    '3': '        b()',
                    '4': '    except Exception as cause:',
                    '5': '        raise NameError(\'a\') from cause',
                    '6': '',
                    '7': ''
                }
            }
        ]

        assert exceptions[2]['message'] == 'c'
        assert exceptions[2]['errorClass'] == 'Exception'
        assert exceptions[2]['type'] == 'python'
        assert exceptions[2]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 16,
                'method': 'c',
                'inProject': True,
                'code': {
                    '13': '',
                    '14': '',
                    '15': 'def c():',
                    '16': '    raise Exception(\'c\')',
                    '17': '',
                    '18': '',
                    '19': 'try:'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 10,
                'method': 'b',
                'inProject': True,
                'code': {
                    '7': '',
                    '8': 'def b():',
                    '9': '    try:',
                    '10': '        c()',
                    '11': '    except Exception as cause:',
                    '12': '        raise ArithmeticError(\'b\') from cause',
                    '13': ''
                }
            }
        ]

    @pytest.mark.skipif(
         sys.version_info < (3, 11),
         reason="requires BaseException.add_note (Python 3.11 or higher)"
    )
    def test_notes(self):
        e = Exception("exception")
        e.add_note("exception note 1")
        e.add_note("exception note 2")
        self.client.notify(e)
        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        metadata = payload['events'][0]['metaData']
        notes = metadata['exception notes']

        assert len(notes) == 2
        assert notes['0'] == "exception note 1"
        assert notes['1'] == "exception note 2"

    def test_chained_exceptions_with_explicit_cause_using_capture_cm(self):
        try:
            with self.client.capture():
                fixtures.raise_exception_with_explicit_cause()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 3

        assert exceptions[0]['message'] == 'a'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'

        assert exceptions[0]['stacktrace'][0]['file'] == \
            'fixtures/caused_by.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'raise_exception_with_explicit_cause'

        assert exceptions[1]['message'] == 'b'
        assert exceptions[1]['errorClass'] == 'ArithmeticError'
        assert exceptions[1]['type'] == 'python'

        assert exceptions[2]['message'] == 'c'
        assert exceptions[2]['errorClass'] == 'Exception'
        assert exceptions[2]['type'] == 'python'

    def test_chained_exceptions_explicit_cause_and_capture_decorator(self):
        @self.client.capture
        def foo():
            fixtures.raise_exception_with_explicit_cause()

        try:
            foo()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 3

        assert exceptions[0]['message'] == 'a'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'

        assert exceptions[0]['stacktrace'][0]['file'] == \
            'fixtures/caused_by.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'raise_exception_with_explicit_cause'

        assert exceptions[1]['message'] == 'b'
        assert exceptions[1]['errorClass'] == 'ArithmeticError'
        assert exceptions[1]['type'] == 'python'

        assert exceptions[2]['message'] == 'c'
        assert exceptions[2]['errorClass'] == 'Exception'
        assert exceptions[2]['type'] == 'python'

    def test_chained_exceptions_with_implicit_cause(self):
        self.client.notify(fixtures.exception_with_implicit_cause)

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 3

        assert exceptions[0]['message'] == 'x'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'
        assert exceptions[0]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 29,
                'method': 'raise_exception_with_implicit_cause',
                'inProject': True,
                'code': {
                    '26': '    try:',
                    '27': '        y()',
                    '28': '    except Exception:',
                    '29': "        raise NameError('x')",
                    '30': '',
                    '31': '',
                    '32': 'def y():'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 44,
                'method': '<module>',
                'inProject': True,
                'code': {
                    '41': '',
                    '42': '',
                    '43': 'try:',
                    '44': '    raise_exception_with_implicit_cause()',
                    '45': 'except Exception as exception:',
                    '46': '    exception_with_implicit_cause = exception',
                    '47': ''
                }
            }
        ]

        assert exceptions[1]['message'] == 'y'
        assert exceptions[1]['errorClass'] == 'ArithmeticError'
        assert exceptions[1]['type'] == 'python'
        assert exceptions[1]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 36,
                'method': 'y',
                'inProject': True,
                'code': {
                    '33': '    try:',
                    '34': '        z()',
                    '35': '    except Exception:',
                    '36': '        raise ArithmeticError(\'y\')',
                    '37': '',
                    '38': '',
                    '39': 'def z():'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 27,
                'method': 'raise_exception_with_implicit_cause',
                'inProject': True,
                'code': {
                    '24': '',
                    '25': 'def raise_exception_with_implicit_cause():',
                    '26': '    try:',
                    '27': '        y()',
                    '28': '    except Exception:',
                    '29': '        raise NameError(\'x\')',
                    '30': ''
                }
            }
        ]

        assert exceptions[2]['message'] == 'z'
        assert exceptions[2]['errorClass'] == 'Exception'
        assert exceptions[2]['type'] == 'python'
        assert exceptions[2]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 40,
                'method': 'z',
                'inProject': True,
                'code': {
                    '37': '',
                    '38': '',
                    '39': 'def z():',
                    '40': '    raise Exception(\'z\')',
                    '41': '',
                    '42': '',
                    '43': 'try:'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 34,
                'method': 'y',
                'inProject': True,
                'code': {
                    '31': '',
                    '32': 'def y():',
                    '33': '    try:',
                    '34': '        z()',
                    '35': '    except Exception:',
                    '36': '        raise ArithmeticError(\'y\')',
                    '37': ''
                }
            }
        ]

    def test_chained_exceptions_with_implicit_cause_using_capture_cm(self):
        try:
            with self.client.capture():
                fixtures.raise_exception_with_implicit_cause()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 3

        assert exceptions[0]['message'] == 'x'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'

        assert exceptions[0]['stacktrace'][0]['file'] == \
            'fixtures/caused_by.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'raise_exception_with_implicit_cause'

        assert exceptions[1]['message'] == 'y'
        assert exceptions[1]['errorClass'] == 'ArithmeticError'
        assert exceptions[1]['type'] == 'python'

        assert exceptions[2]['message'] == 'z'
        assert exceptions[2]['errorClass'] == 'Exception'
        assert exceptions[2]['type'] == 'python'

    def test_chained_exceptions_implicit_cause_and_capture_decorator(self):
        @self.client.capture
        def foo():
            fixtures.raise_exception_with_implicit_cause()

        try:
            foo()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 3

        assert exceptions[0]['message'] == 'x'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'

        assert exceptions[0]['stacktrace'][0]['file'] == \
            'fixtures/caused_by.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'raise_exception_with_implicit_cause'

        assert exceptions[1]['message'] == 'y'
        assert exceptions[1]['errorClass'] == 'ArithmeticError'
        assert exceptions[1]['type'] == 'python'

        assert exceptions[2]['message'] == 'z'
        assert exceptions[2]['errorClass'] == 'Exception'
        assert exceptions[2]['type'] == 'python'

    def test_chained_exceptions_with_no_cause(self):
        self.client.notify(fixtures.exception_with_no_cause)

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 1

        assert exceptions[0]['message'] == 'one'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'
        assert exceptions[0]['stacktrace'] == [
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 53,
                'method': 'raise_exception_with_no_cause',
                'inProject': True,
                'code': {
                    '50': '    try:',
                    '51': '        two()',
                    '52': '    except Exception:',
                    '53': "        raise NameError('one') from None",
                    '54': '',
                    '55': '',
                    '56': 'def two():'
                }
            },
            {
                'file': 'fixtures/caused_by.py',
                'lineNumber': 68,
                'method': '<module>',
                'inProject': True,
                'code': {
                    '64': "    raise Exception('three')",
                    '65': '',
                    '66': '',
                    '67': 'try:',
                    '68': '    raise_exception_with_no_cause()',
                    '69': 'except Exception as exception:',
                    '70': '    exception_with_no_cause = exception'
                }
            }
        ]

    def test_chained_exceptions_with_no_cause_using_capture_decorator(self):
        @self.client.capture
        def foo():
            fixtures.raise_exception_with_no_cause()

        try:
            foo()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 1

        assert exceptions[0]['message'] == 'one'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'

        assert exceptions[0]['stacktrace'][0]['file'] == \
            'fixtures/caused_by.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'raise_exception_with_no_cause'

    def test_chained_exceptions_with_no_cause_using_capture_cm(self):
        try:
            with self.client.capture():
                fixtures.raise_exception_with_no_cause()
        except Exception:
            pass

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 1

        assert exceptions[0]['message'] == 'one'
        assert exceptions[0]['errorClass'] == 'NameError'
        assert exceptions[0]['type'] == 'python'

        assert exceptions[0]['stacktrace'][0]['file'] == \
            'fixtures/caused_by.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'raise_exception_with_no_cause'

    def test_notify_with_string(self):
        """
        Ensure passing a string to 'notify' doesn't crash
        This isn't an intended use-case but, as it works, it's important to
        test so we can preserve BC
        """
        self.client.notify('not an exception!')

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        exceptions = payload['events'][0]['exceptions']

        assert len(exceptions) == 1

        assert exceptions[0]['message'] == 'not an exception!'
        assert exceptions[0]['errorClass'] == 'str'

        assert exceptions[0]['stacktrace'][0]['file'] == 'test_client.py'
        assert exceptions[0]['stacktrace'][0]['inProject']
        assert exceptions[0]['stacktrace'][0]['method'] == \
            'test_notify_with_string'

    def test_ignore_classes_checks_exception_chain_with_explicit_cause(self):
        self.client.configuration.ignore_classes = ['ArithmeticError']
        self.client.notify(fixtures.exception_with_explicit_cause)

        assert self.sent_report_count == 0

        self.client.configuration.ignore_classes = []
        self.client.notify(fixtures.exception_with_explicit_cause)

        assert self.sent_report_count == 1

    def test_ignore_classes_checks_exception_chain_with_implicit_cause(self):
        self.client.configuration.ignore_classes = ['ArithmeticError']
        self.client.notify(fixtures.exception_with_implicit_cause)

        assert self.sent_report_count == 0

        self.client.configuration.ignore_classes = []
        self.client.notify(fixtures.exception_with_implicit_cause)

        assert self.sent_report_count == 1

    def test_ignore_classes_has_no_exception_chain_with_no_cause(self):
        self.client.configuration.ignore_classes = ['ArithmeticError']
        self.client.notify(fixtures.exception_with_no_cause)

        assert self.sent_report_count == 1

    def test_skip_bugsnag_attr_prevents_notify_when_true(self):
        exception = Exception('Testing Notify')
        self.client.notify(exception)

        assert self.sent_report_count == 1

        exception.skip_bugsnag = True
        self.client.notify(exception)

        assert self.sent_report_count == 1

    def test_setting_skip_bugsnag_attr_to_false_allows_notify(self):
        exception = Exception('Testing Notify')
        exception.skip_bugsnag = True

        self.client.notify(exception)

        assert self.sent_report_count == 0

        exception.skip_bugsnag = False
        self.client.notify(exception)

        assert self.sent_report_count == 1

    def test_deleting_skip_bugsnag_attr_allows_notify(self):
        exception = Exception('Testing Notify')
        exception.skip_bugsnag = True

        self.client.notify(exception)

        assert self.sent_report_count == 0

        delattr(exception, 'skip_bugsnag')
        self.client.notify(exception)

        assert self.sent_report_count == 1

    def test_feature_flags_can_be_added_individually(self):
        self.client.add_feature_flag('one')
        self.client.add_feature_flag('two', 'a')
        self.client.add_feature_flag('three', None)

        assert self.client.feature_flags == [
            FeatureFlag('one'),
            FeatureFlag('two', 'a'),
            FeatureFlag('three')
        ]

    def test_feature_flags_can_be_added_in_bulk(self):
        self.client.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        assert self.client.feature_flags == [
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ]

    def test_feature_flags_can_be_removed_individually(self):
        self.client.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        self.client.clear_feature_flag('b')

        assert self.client.feature_flags == [
            FeatureFlag('a', '1'),
            FeatureFlag('c', '3')
        ]

    def test_feature_flags_can_be_cleared(self):
        self.client.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        self.client.clear_feature_flags()

        assert self.client.feature_flags == []

    def test_feature_flags_can_be_added_individually_with_legacy_client(self):
        legacy.add_feature_flag('one')
        legacy.add_feature_flag('two', 'a')
        legacy.add_feature_flag('three', None)

        assert legacy.default_client.feature_flags == [
            FeatureFlag('one'),
            FeatureFlag('two', 'a'),
            FeatureFlag('three')
        ]

    def test_feature_flags_can_be_added_in_bulk_with_legacy_client(self):
        legacy.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        assert legacy.default_client.feature_flags == [
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ]

    def test_feature_flags_can_be_removed_with_legacy_client(self):
        legacy.add_feature_flags([
            FeatureFlag('x', '1'),
            FeatureFlag('y'),
            FeatureFlag('z', '3')
        ])

        legacy.clear_feature_flag('y')

        assert legacy.default_client.feature_flags == [
            FeatureFlag('x', '1'),
            FeatureFlag('z', '3')
        ]

    def test_feature_flags_can_be_cleared_with_legacy_client(self):
        legacy.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        legacy.clear_feature_flags()

        assert legacy.default_client.feature_flags == []

    def test_feature_flags_are_included_in_payload(self):
        self.client.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        self.client.notify(Exception('abc'))

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == [
            {'featureFlag': 'a', 'variant': '1'},
            {'featureFlag': 'b'},
            {'featureFlag': 'c', 'variant': '3'}
        ]

    def test_mutating_client_feature_flags_does_not_affect_event(self):
        self.client.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        def on_error(event):
            # adding a flag to the event directly should affect the payload
            event.add_feature_flag('d')

            # adding a flag to the client should not affect the payload as the
            # event has already been created
            self.client.add_feature_flag('e')

        self.client.configuration.middleware.before_notify(on_error)
        self.client.notify(Exception('abc'))

        assert self.sent_report_count == 1

        payload = self.server.events_received[0]['json_body']
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == [
            {'featureFlag': 'a', 'variant': '1'},
            {'featureFlag': 'b'},
            {'featureFlag': 'c', 'variant': '3'},
            {'featureFlag': 'd'}
        ]

        assert self.client.feature_flags == [
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3'),
            FeatureFlag('e')
        ]


@pytest.mark.parametrize("metadata,type", [
    (1234, 'int'),
    ('abc', 'str'),
    ([1, 2, 3], 'list'),
    (True, 'bool'),
    (False, 'bool'),
    (None, 'NoneType'),
    (object(), 'object')
])
def test_breadcrumb_metadata_is_coerced_to_dict(metadata, type):
    client = Client()
    assert len(client.configuration.breadcrumbs) == 0

    with pytest.warns(RuntimeWarning) as warnings:
        client.leave_breadcrumb('abcxyz', metadata=metadata)

    expected_message = 'breadcrumb metadata must be a dict, got ' + type

    assert len(warnings) == 1
    assert warnings[0].message.args[0] == expected_message

    assert len(client.configuration.breadcrumbs) == 1

    breadcrumb = client.configuration.breadcrumbs[0]

    assert breadcrumb.message == 'abcxyz'
    assert breadcrumb.metadata == {}
    assert breadcrumb.type == BreadcrumbType.MANUAL
    assert is_valid_timestamp(breadcrumb.timestamp)
