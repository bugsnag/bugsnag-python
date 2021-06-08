import os
import re
import sys
import pytest
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from bugsnag import (
    Client,
    Configuration,
    BreadcrumbType,
    Breadcrumb
)

import bugsnag.legacy as legacy
from tests.utils import IntegrationTest, ScaryException

timestamp_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}(?:[+-]\d{2}:\d{2}|Z)'  # noqa: E501


def is_valid_timestamp(timestamp: str) -> bool:
    return bool(re.search(timestamp_regex, timestamp))


class ClientTest(IntegrationTest):
    def setUp(self):
        super(ClientTest, self).setUp()

        self.client = Client(api_key='testing client key',
                             endpoint=self.server.url,
                             project_root=os.path.join(os.getcwd(), 'tests'),
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

    # Sending Event

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
        c.configure(delivery=44, api_key='abc')
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
        client1 = Client(api_key='abc', asynchronous=False,
                         endpoint=self.server.url)
        client2 = Client(api_key='456', asynchronous=False,
                         endpoint=self.server.url)

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

        client1 = Client(api_key='abc', asynchronous=False,
                         endpoint=self.server.url)
        Client(api_key='456', asynchronous=False, endpoint=self.server.url,
               install_sys_hook=False)

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

    def test_leave_breadcrumb_with_string_type(self):
        client = Client()
        assert len(client.configuration.breadcrumbs) == 0

        client.leave_breadcrumb('abcxyz', type='log')
        assert len(client.configuration.breadcrumbs) == 1

        breadcrumb = client.configuration.breadcrumbs[0]

        assert breadcrumb.message == 'abcxyz'
        assert breadcrumb.metadata == {}
        assert breadcrumb.type == BreadcrumbType.LOG
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
        assert len(self.server.received) == 0

        self.client.leave_breadcrumb('breadcrumb 1')
        self.client.leave_breadcrumb('breadcrumb 2', type=BreadcrumbType.USER)
        self.client.leave_breadcrumb('breadcrumb 3', metadata={'a': 1, 'b': 2})

        self.client.notify(Exception('hello'))

        assert len(self.server.received) == 1

        payload = self.server.received[0]['json_body']
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

    def test_can_modify_breadcrumbs_in_before_notify_callbacks(self):
        assert len(self.server.received) == 0

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

        assert len(self.server.received) == 1

        payload = self.server.received[0]['json_body']
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
