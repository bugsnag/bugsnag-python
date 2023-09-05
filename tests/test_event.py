from importlib import reload
import inspect
import json
import os
import sys
import unittest

import pytest
from bugsnag.breadcrumbs import Breadcrumb, BreadcrumbType
from bugsnag.configuration import Configuration
from bugsnag.event import Event
from bugsnag.feature_flags import FeatureFlag
from tests import fixtures


class TestEvent(unittest.TestCase):
    event_class = Event

    def test_sanitize(self):
        """
            It should sanitize request data
        """
        config = Configuration()
        event = self.event_class(Exception("oops"), config, {},
                                 request={"params": {"password": "secret"}})

        event.add_tab("request", {"arguments": {"password": "secret"}})

        payload = json.loads(event._payload())
        request = payload['events'][0]['metaData']['request']
        self.assertEqual(request['arguments']['password'], '[FILTERED]')
        self.assertEqual(request['params']['password'], '[FILTERED]')

    def test_code(self):
        """
            It should include code
        """
        config = Configuration()
        line = inspect.currentframe().f_lineno + 1
        event = self.event_class(Exception("oops"), config, {})

        payload = json.loads(event._payload())

        code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']
        lvl = "        "
        self.assertEqual(code[str(line - 3)], lvl + "\"\"\"")
        self.assertEqual(code[str(line - 2)], lvl + "config = Configuration()")
        self.assertEqual(code[str(line - 1)],
                         lvl + "line = inspect.currentframe().f_lineno + 1")
        self.assertEqual(
            code[str(line)],
            lvl +
            "event = self.event_class(Exception(\"oops\"), config, {})"
            )
        self.assertEqual(code[str(line + 1)], "")
        self.assertEqual(code[str(line + 2)],
                         lvl + "payload = json.loads(event._payload())")
        self.assertEqual(code[str(line + 3)], "")

    def test_a_source_function_can_be_provided(self):
        def some_function():
            print("hello")
            print("world")

        config = Configuration()
        event = self.event_class(
            Exception("oops"),
            config,
            {},
            source_func=some_function
        )

        payload = json.loads(event._payload())

        stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']
        frame = stacktrace[-1]

        assert frame['file'] == 'tests/test_event.py'
        assert frame['lineNumber'] == inspect.getsourcelines(some_function)[1]
        assert frame['method'] == 'some_function'
        assert frame['inProject']

    def test_source_function_is_ignored_when_invalid(self):
        not_actually_a_function = 12345

        config = Configuration()
        event = self.event_class(
            Exception("oops"),
            config,
            {},
            source_func=not_actually_a_function
        )

        payload = json.loads(event._payload())

        stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']

        # the first frame should be this test method
        assert stacktrace[0]['file'] == 'tests/test_event.py'
        assert stacktrace[0]['method'] == inspect.currentframe().f_code.co_name

        # the rest of the trace shouldn't be in this file
        for frame in stacktrace[1:]:
            assert frame['file'] != 'tests/test_event.py'
            assert frame['method'] != 'not_actually_a_function'

    def test_a_traceback_can_be_provided(self):
        def get_traceback():
            try:
                raise Exception('abc')
            except Exception as exception:
                return exception.__traceback__

        traceback = get_traceback()

        config = Configuration()
        event = self.event_class(
            Exception("oops"),
            config,
            {},
            traceback=traceback
        )

        payload = json.loads(event._payload())

        stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']

        # there's only one frame in 'traceback' - the call to 'get_traceback'
        assert len(stacktrace) == 1

        frame = stacktrace[0]

        # the expected line number is the 'raise', which is the second line of
        # the 'get_traceback' function - hence '+ 2'
        line = inspect.getsourcelines(get_traceback)[1] + 2

        assert frame['file'] == 'tests/test_event.py'
        assert frame['lineNumber'] == line
        assert frame['method'] == 'get_traceback'
        assert frame['inProject']

    def test_code_at_start_of_file(self):

        config = Configuration()
        event = self.event_class(fixtures.start_of_file[1], config, {},
                                 traceback=fixtures.start_of_file[2])

        payload = json.loads(event._payload())

        code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']
        self.assertEqual(
            {'1': '# flake8: noqa',
             '2': 'try:',
             '3': '    import sys; raise Exception("start")',
             '4': 'except Exception: start_of_file = sys.exc_info()',
             '5': '# 4',
             '6': '# 5',
             '7': '# 6'}, code)

    def test_code_at_end_of_file(self):

        config = Configuration()
        event = self.event_class(fixtures.end_of_file[1], config, {},
                                 traceback=fixtures.end_of_file[2])

        payload = json.loads(event._payload())

        code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']
        self.assertEqual(
            {'6':  '# 5',
             '7':  '# 6',
             '8':  '# 7',
             '9':  '# 8',
             '10': 'try:',
             '11': '    import sys; raise Exception("end")',
             '12': 'except Exception: end_of_file = sys.exc_info()'}, code)

    def test_code_turned_off(self):
        config = Configuration()
        config.send_code = False
        event = self.event_class(Exception("oops"), config, {},
                                 traceback=fixtures.end_of_file[2])

        payload = json.loads(event._payload())

        code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']
        self.assertEqual(code, None)

    def test_no_traceback_exclude_modules(self):
        from tests.fixtures import helpers
        config = Configuration()
        config.configure(project_root=os.path.join(os.getcwd(), 'tests'))

        event = helpers.invoke_exception_on_other_file(config)

        payload = json.loads(event._payload())
        exception = payload['events'][0]['exceptions'][0]
        first_traceback = exception['stacktrace'][0]

        self.assertEqual(first_traceback['file'], 'fixtures/helpers.py')
        self.assertEqual(
            {
                '1': 'def invoke_exception_on_other_file(config):',
                '2': '    from bugsnag.event import Event',
                '3': '',
                '4': '    return Event(Exception("another file!"), config, {})'
            },
            first_traceback['code']
        )

    def test_traceback_exclude_modules(self):
        # Make sure samples.py is compiling to pyc
        import py_compile
        py_compile.compile('./tests/fixtures/helpers.py')

        from tests.fixtures import helpers
        reload(helpers)  # .py variation might be loaded from previous test.

        if sys.version_info < (3, 0):
            # Python 2.6 & 2.7 returns the cached file on __file__,
            # and hence we verify it returns .pyc for these versions
            # and the code at _generate_stacktrace() handles that.
            self.assertTrue(helpers.__file__.endswith('.pyc'))

        config = Configuration()
        config.configure(project_root=os.path.join(os.getcwd(), 'tests'))
        config.traceback_exclude_modules = [helpers]

        event = helpers.invoke_exception_on_other_file(config)

        payload = json.loads(event._payload())
        exception = payload['events'][0]['exceptions'][0]
        first_traceback = exception['stacktrace'][0]
        self.assertEqual(first_traceback['file'], 'test_event.py')

    def test_stacktrace_can_be_reassigned(self):
        config = Configuration()
        event = self.event_class(Exception("oops"), config, {})

        expected_stacktrace = [
            {
                'file': '/a/b/c/one.py',
                'lineNumber': 1234,
                'method': 'do_stuff',
                'inProject': True,
                'code': {'1234': 'def do_stuff():'},
            },
            {
                'file': '/a/b/c/two.py',
                'lineNumber': 9876,
                'method': 'do_other_stuff',
                'inProject': False,
                'code': {'9876': 'def do_other_stuff():'},
            }
        ]

        with pytest.warns(DeprecationWarning) as records:
            event.stacktrace = expected_stacktrace

            assert len(records) == 1
            assert str(records[0].message) == (
                'The Event "stacktrace" property has been deprecated in favour'
                ' of accessing the stacktrace of an error, for example '
                '"errors[0].stacktrace"'
            )

        payload = json.loads(event._payload())
        actual_stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']

        assert actual_stacktrace == expected_stacktrace

    def test_stacktrace_can_be_mutated(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        with pytest.warns(DeprecationWarning) as records:
            event.stacktrace[0]['file'] = '/abc/xyz.py'

            assert len(records) == 1
            assert str(records[0].message) == (
                'The Event "stacktrace" property has been deprecated in favour'
                ' of accessing the stacktrace of an error, for example '
                '"errors[0].stacktrace"'
            )

        payload = json.loads(event._payload())
        stacktrace = payload['events'][0]['exceptions'][0]['stacktrace']

        assert stacktrace[0]['file'] == '/abc/xyz.py'

    def test_original_exception_can_be_reassigned(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        with pytest.warns(DeprecationWarning) as records:
            event.exception = KeyError('ahhh')

            assert len(records) == 1
            assert str(records[0].message) == (
                'Setting the Event "exception" property has been deprecated, '
                'update the "errors" list instead'
            )

        payload = json.loads(event._payload())
        exception = payload['events'][0]['exceptions'][0]

        assert exception['message'] == "'ahhh'"
        assert exception['errorClass'] == 'KeyError'

    def test_device_data(self):
        """
            It should include device data
        """
        config = Configuration()
        config.hostname = 'test_host_name'
        config.runtime_versions = {'python': '9.9.9'}
        event = self.event_class(Exception("oops"), config, {})

        payload = json.loads(event._payload())

        device = payload['events'][0]['device']
        self.assertEqual('test_host_name', device['hostname'])
        self.assertEqual('9.9.9', device['runtimeVersions']['python'])

    def test_default_app_type(self):
        """
        app_type is None by default
        """
        config = Configuration()
        event = self.event_class(Exception("oops"), config, {})
        payload = json.loads(event._payload())
        app = payload['events'][0]['app']

        assert app['type'] is None

    def test_configured_app_type(self):
        """
        It should include app type if specified
        """
        config = Configuration()
        config.configure(app_type='rq')
        event = self.event_class(Exception("oops"), config, {})
        payload = json.loads(event._payload())
        app = payload['events'][0]['app']

        assert app['type'] == 'rq'

    def test_default_request(self):
        config = Configuration()
        config.configure(app_type='rq')
        event = self.event_class(Exception("oops"), config, {})
        assert event.request is None

    def test_meta_data_warning(self):
        config = Configuration()
        with pytest.warns(DeprecationWarning) as records:
            event = self.event_class(Exception('oh no'), config, {},
                                     meta_data={'nuts': {'almonds': True}})

            assert len(records) > 0
            i = len(records) - 1
            assert str(records[i].message) == ('The Event "meta_data" ' +
                                               'argument has been replaced ' +
                                               'with "metadata"')
            assert event.metadata['nuts']['almonds']

    def test_breadcrumbs_are_read_from_configuration(self):
        breadcrumb = Breadcrumb('example', BreadcrumbType.LOG, {'a': 1}, 'now')

        config = Configuration()
        config._breadcrumbs.append(breadcrumb)

        event = self.event_class(Exception('oops'), config, {})

        assert len(event.breadcrumbs) == 1
        assert event.breadcrumbs[0].to_dict() == breadcrumb.to_dict()

    def test_adding_new_breadcrumbs_does_not_change_past_events(self):
        breadcrumb1 = Breadcrumb('1', BreadcrumbType.LOG, {'a': 1}, 'now')

        config = Configuration()
        config._breadcrumbs.append(breadcrumb1)

        event1 = self.event_class(Exception('oops'), config, {})

        breadcrumb2 = Breadcrumb('2', BreadcrumbType.USER, {'b': 2}, 'then')
        config._breadcrumbs.append(breadcrumb2)

        event2 = self.event_class(Exception('oh no'), config, {})

        breadcrumb3 = Breadcrumb('3', BreadcrumbType.USER, {'c': 3}, 'then')
        config._breadcrumbs.append(breadcrumb3)

        event3 = self.event_class(Exception('oh dear'), config, {})

        assert len(event1.breadcrumbs) == 1
        assert len(event2.breadcrumbs) == 2
        assert len(event3.breadcrumbs) == 3

        assert event1.breadcrumbs[0].to_dict() == breadcrumb1.to_dict()

        assert event2.breadcrumbs[0].to_dict() == breadcrumb1.to_dict()
        assert event2.breadcrumbs[1].to_dict() == breadcrumb2.to_dict()

        assert event3.breadcrumbs[0].to_dict() == breadcrumb1.to_dict()
        assert event3.breadcrumbs[1].to_dict() == breadcrumb2.to_dict()
        assert event3.breadcrumbs[2].to_dict() == breadcrumb3.to_dict()

    def test_mutating_breadcrumb_list_does_not_mutate_event(self):
        breadcrumb = Breadcrumb('example', BreadcrumbType.LOG, {'a': 1}, 'now')

        config = Configuration()
        config._breadcrumbs.append(breadcrumb)

        event = self.event_class(Exception('oops'), config, {})

        assert len(event.breadcrumbs) == 1
        assert event.breadcrumbs[0].to_dict() == breadcrumb.to_dict()

        event.breadcrumbs.append('haha')

        assert len(event.breadcrumbs) == 1
        assert event.breadcrumbs[0].to_dict() == breadcrumb.to_dict()

    def test_breadcrumbs_are_included_in_payload(self):
        breadcrumb1 = Breadcrumb('one', BreadcrumbType.LOG, {'a': 1}, 'now')
        breadcrumb2 = Breadcrumb('two', BreadcrumbType.USER, {'b': 2}, 'now')

        config = Configuration()
        config._breadcrumbs.append(breadcrumb1)
        config._breadcrumbs.append(breadcrumb2)

        event = self.event_class(Exception('oops'), config, {})

        payload = json.loads(event._payload())

        assert len(payload['events'][0]['breadcrumbs']) == 2

        payload_breadcrumb1 = payload['events'][0]['breadcrumbs'][0]
        payload_breadcrumb2 = payload['events'][0]['breadcrumbs'][1]

        assert breadcrumb1.to_dict() == payload_breadcrumb1
        assert breadcrumb2.to_dict() == payload_breadcrumb2

    def test_breadcrumb_array_is_always_in_payload(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        payload = json.loads(event._payload())

        assert payload['events'][0]['breadcrumbs'] == []

    def test_feature_flags_can_be_added_individually(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        assert event.feature_flags == []

        event.add_feature_flag('one')
        event.add_feature_flag('two', 'a')
        event.add_feature_flag('three', None)

        assert event.feature_flags == [
            FeatureFlag('one'),
            FeatureFlag('two', 'a'),
            FeatureFlag('three')
        ]

    def test_feature_flags_can_be_added_in_bulk(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        assert event.feature_flags == []

        event.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        assert event.feature_flags == [
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ]

    def test_feature_flags_can_be_removed_individually(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        assert event.feature_flags == []

        event.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        event.clear_feature_flag('b')

        assert event.feature_flags == [
            FeatureFlag('a', '1'),
            FeatureFlag('c', '3')
        ]

    def test_feature_flags_can_be_cleared(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        assert event.feature_flags == []

        event.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        event.clear_feature_flags()

        assert event.feature_flags == []

    def test_feature_flags_are_included_in_payload(self):
        config = Configuration()
        event = self.event_class(Exception('oops'), config, {})

        assert event.feature_flags == []

        event.add_feature_flags([
            FeatureFlag('a', '1'),
            FeatureFlag('b'),
            FeatureFlag('c', '3')
        ])

        payload = json.loads(event._payload())
        feature_flags = payload['events'][0]['featureFlags']

        assert feature_flags == [
            {'featureFlag': 'a', 'variant': '1'},
            {'featureFlag': 'b'},
            {'featureFlag': 'c', 'variant': '3'}
        ]
