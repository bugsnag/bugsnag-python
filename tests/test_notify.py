# -*- coding: utf8 -*-

import sys
import time

import pytest
import bugsnag
from pathlib import Path
from tests import fixtures
from tests.utils import ScaryException, IntegrationTest
from tests.fixtures import samples


class TestBugsnag(IntegrationTest):

    def setUp(self):
        super(TestBugsnag, self).setUp()
        bugsnag.configure(
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            api_key='tomatoes',
            notify_release_stages=['dev'],
            release_stage='dev',
            asynchronous=False,
        )

    def test_asynchronous_notify(self):
        bugsnag.configure(asynchronous=True)
        self.server.paused = True
        bugsnag.notify(ScaryException('unexpected failover'))
        self.server.paused = False

        start = time.time()
        while len(self.server.events_received) == 0:
            if time.time() > (start + 0.5):
                raise Exception(
                    'Timed out while waiting for asynchronous request.')

            time.sleep(0.001)

        self.assertEqual(len(self.server.events_received), 1)

    def test_notify_method(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        request = self.server.events_received[0]
        self.assertEqual('POST', request['method'])

    def test_notify_request_count(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        self.assertEqual(1, len(self.server.events_received))

    def test_notify_configured_api_key(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        headers = self.server.events_received[0]['headers']
        self.assertEqual('tomatoes', headers['Bugsnag-Api-Key'])

    def test_notify_configured_release_stage(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('dev', event['releaseStage'])

    def test_notify_unconfigured_release_stage(self):
        bugsnag.configure(release_stage='pickles')
        bugsnag.notify(ScaryException('unexpected failover'))
        self.assertEqual(0, len(self.server.events_received))

    def test_notify_default_severity(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('warning', event['severity'])

    def test_notify_override_severity(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       severity='info')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('info', event['severity'])

    def test_notify_configured_app_version(self):
        bugsnag.configure(app_version='343.2.10')
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('343.2.10', event['app']['version'])

    def test_notify_override_context(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       context='/some/path')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('/some/path', event['context'])

    def test_notify_override_grouping_hash(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       grouping_hash='Callout errors')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('Callout errors', event['groupingHash'])

    def test_notify_override_user(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       user={'name': 'bob',
                             'email': 'mcbob@example.com',
                             'id': '542347329'})
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('bob', event['user']['name'])
        self.assertEqual('542347329', event['user']['id'])
        self.assertEqual('mcbob@example.com', event['user']['email'])

    def test_notify_configured_hostname(self):
        bugsnag.configure(hostname='I_AM_ROOT')
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('I_AM_ROOT', event['device']['hostname'])

    def test_notify_override_metadata_sections(self):
        bugsnag.add_metadata_tab('food', {'beans': 3, 'corn': 'purple'})
        bugsnag.notify(ScaryException('unexpected failover'),
                       metadata={'food': {'beans': 5}, 'skills': {'spear': 6}})
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(6, event['metaData']['skills']['spear'])
        self.assertEqual('purple', event['metaData']['food']['corn'])
        self.assertEqual(5, event['metaData']['food']['beans'])

    def test_notify_configured_metadata_sections(self):
        bugsnag.add_metadata_tab('food', {'beans': 3, 'corn': 'purple'})
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('purple', event['metaData']['food']['corn'])
        self.assertEqual(3, event['metaData']['food']['beans'])

    def test_notify_metadata_filter(self):
        bugsnag.configure(params_filters=['apple', 'grape'])
        bugsnag.notify(ScaryException('unexpected failover'),
                       apple='four', cantaloupe='green')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('[FILTERED]', event['metaData']['custom']['apple'])
        self.assertEqual('green', event['metaData']['custom']['cantaloupe'])

    def test_notify_device_filter(self):
        bugsnag.configure(params_filters=['hostname'])
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('[FILTERED]', event['device']['hostname'])

    def test_notify_user_filter(self):
        bugsnag.configure(params_filters=['address', 'phonenumber'])
        bugsnag.notify(ScaryException('unexpected failover'),
                       user={
                           "id": "test-man",
                           "address": "123 street\n cooltown\n ABC 123",
                           "phonenumber": "12345678900",
                           "firstname": "Test",
                           "lastname": "Man"
                           })
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('[FILTERED]', event['user']['address'])
        self.assertEqual('[FILTERED]', event['user']['phonenumber'])
        self.assertEqual('test-man', event['user']['id'])
        self.assertEqual('Test', event['user']['firstname'])
        self.assertEqual('Man', event['user']['lastname'])

    def test_notify_payload_matching_filter(self):
        bugsnag.configure(params_filters=['bar'])
        bugsnag.notify(ScaryException('unexpected failover'), foo=4, bar=76)

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]

        self.assertEqual(4, event['metaData']['custom']['foo'])
        self.assertEqual('[FILTERED]', event['metaData']['custom']['bar'])
        self.assertEqual(174, exception['stacktrace'][0]['lineNumber'])

    def test_notify_ignore_class(self):
        bugsnag.configure(ignore_classes=['tests.utils.ScaryException'])
        bugsnag.notify(ScaryException('unexpected failover'))
        self.assertEqual(0, len(self.server.events_received))

    def test_notify_ignore_class_nested(self):
        bugsnag.configure(
            ignore_classes=['tests.utils.ScaryException.NestedScaryException'])
        bugsnag.notify(ScaryException.NestedScaryException('nested'))
        self.assertEqual(0, len(self.server.events_received))

    def test_ignore_classes_checks_exception_chain_with_explicit_cause(self):
        bugsnag.configure(ignore_classes=['ArithmeticError'])
        bugsnag.notify(fixtures.exception_with_explicit_cause)

        assert self.sent_report_count == 0

        bugsnag.configure(ignore_classes=[])
        bugsnag.notify(fixtures.exception_with_explicit_cause)

        assert self.sent_report_count == 1

    def test_ignore_classes_checks_exception_chain_with_implicit_cause(self):
        bugsnag.configure(ignore_classes=['ArithmeticError'])
        bugsnag.notify(fixtures.exception_with_implicit_cause)

        assert self.sent_report_count == 0

        bugsnag.configure(ignore_classes=[])
        bugsnag.notify(fixtures.exception_with_implicit_cause)

        assert self.sent_report_count == 1

    def test_ignore_classes_has_no_exception_chain_with_no_cause(self):
        bugsnag.configure(ignore_classes=['ArithmeticError'])
        bugsnag.notify(fixtures.exception_with_no_cause)

        assert self.sent_report_count == 1

    def test_notify_configured_invalid_api_key(self):
        config = bugsnag.configure()
        config.api_key = None
        bugsnag.notify(ScaryException('unexpected failover'))
        self.assertEqual(0, len(self.server.events_received))

    def test_notify_custom_app_type(self):
        bugsnag.notify(ScaryException('unexpected failover'), app_type='work')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('work', event['app']['type'])

    def test_notify_callback_app_type(self):

        def callback(report):
            report.app_type = 'whopper'

        bugsnag.configure(app_type='rq')
        bugsnag.before_notify(callback)
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('whopper', event['app']['type'])

    def test_notify_configured_app_type(self):
        bugsnag.configure(app_type='rq')
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('rq', event['app']['type'])

    def test_notify_sends_when_before_notify_throws(self):

        def callback(report):
            report.add_custom_data('foo', 'bar')
            raise ScaryException('oh no')

        bugsnag.before_notify(callback)
        bugsnag.notify(ScaryException('unexpected failover'))
        self.assertEqual(1, len(self.server.events_received))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('bar', event['metaData']['custom']['foo'])

    def test_notify_before_notify_remove_api_key(self):

        def callback(report):
            report.api_key = None

        bugsnag.before_notify(callback)
        bugsnag.notify(ScaryException('unexpected failover'))
        self.assertEqual(0, len(self.server.events_received))

    def test_notify_before_notify_modifying_api_key(self):

        def callback(report):
            report.api_key = 'sandwich'

        bugsnag.before_notify(callback)
        bugsnag.notify(ScaryException('unexpected failover'))
        headers = self.server.events_received[0]['headers']
        self.assertEqual('sandwich', headers['Bugsnag-Api-Key'])

    def test_notify_before_notify_modifying_metadata(self):

        def callback(report):
            report.metadata['foo'] = {'sandwich': 'bar'}

        bugsnag.before_notify(callback)
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('bar', event['metaData']['foo']['sandwich'])

    def test_notify_before_notify_add_custom_data(self):

        def callback(report):
            report.add_custom_data('color', 'green')

        bugsnag.before_notify(callback)
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('green', event['metaData']['custom']['color'])

    def test_notify_configured_lib_root(self):
        bugsnag.configure(lib_root='/the/basement')
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('/the/basement', event['libRoot'])

    def test_notify_configured_project_root(self):
        bugsnag.configure(project_root='/the/basement')
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('/the/basement', event['projectRoot'])

    def test_notify_configured_project_root_using_path_object(self):
        bugsnag.configure(project_root=Path('/the/basement'))
        bugsnag.notify(ScaryException('unexpected failover'))

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        assert event['projectRoot'] == '/the/basement'

    def test_notify_invalid_severity(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       severity='debug')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('warning', event['severity'])

    def test_notify_override_deprecated_user_id(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       user_id='542347329')
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('542347329', event['user']['id'])

    def test_notify_override_api_key(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       api_key='gravy!')
        headers = self.server.events_received[0]['headers']
        self.assertEqual('gravy!', headers['Bugsnag-Api-Key'])

    def test_notify_payload_version(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        headers = self.server.events_received[0]['headers']
        self.assertEqual('4.0', headers['Bugsnag-Payload-Version'])

    def test_notify_error_class(self):
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('tests.utils.ScaryException', exception['errorClass'])

    def test_notify_bad_encoding_metadata(self):

        class BadThings:

            def __str__(self):
                raise Exception('nah')

        bugsnag.notify(ScaryException('unexpected failover'), bad=BadThings())
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('[BADENCODING]', event['metaData']['custom']['bad'])

    def test_notify_recursive_metadata_dict(self):
        a = {'foo': 'bar'}
        a['baz'] = a
        bugsnag.add_metadata_tab('a', a)
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('bar', event['metaData']['a']['foo'])
        self.assertEqual('[RECURSIVE]', event['metaData']['a']['baz']['baz'])

    def test_notify_recursive_metadata_array(self):
        a = ['foo', 'bar']
        a.append(a)
        bugsnag.add_metadata_tab('a', {'b': a})
        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(['foo', 'bar', '[RECURSIVE]'],
                         event['metaData']['a']['b'])

    def test_notify_metadata_bool_value(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       value=True, value2=False)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(True, event['metaData']['custom']['value'])
        self.assertEqual(False, event['metaData']['custom']['value2'])

    def test_notify_metadata_complex_value(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       value=(5 + 0j), value2=(13 + 3.4j))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('(5+0j)', event['metaData']['custom']['value'])
        self.assertEqual('(13+3.4j)', event['metaData']['custom']['value2'])

    def test_notify_non_exception(self):
        bugsnag.notify(2)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual(1, len(self.server.events_received))
        self.assertEqual('RuntimeError', exception['errorClass'])
        self.assertTrue(repr(2) in exception['message'])

    def test_notify_bad_encoding_exception_tuple(self):

        class BadThings:

            def __repr__(self):
                raise Exception('nah')

        bugsnag.notify(BadThings())
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('[BADENCODING]', exception['message'])

    def test_notify_single_value_tuple(self):
        bugsnag.notify((None,))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual(1, len(self.server.events_received))
        self.assertEqual('RuntimeError', exception['errorClass'])
        self.assertTrue(repr(None) in exception['message'])

    def test_notify_invalid_values_tuple(self):
        bugsnag.notify((None, 2, "foo"))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual(1, len(self.server.events_received))
        self.assertEqual('RuntimeError', exception['errorClass'])
        self.assertTrue(repr(2) in exception['message'])

    def test_notify_exception_with_traceback_option(self):
        backtrace = None
        try:
            raise ScaryException('foo')
        except ScaryException:
            backtrace = sys.exc_info()[2]

        bugsnag.notify(Exception("foo"), traceback=backtrace)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        stacktrace = exception['stacktrace']
        self.assertEqual(1, len(self.server.events_received))
        self.assertEqual('foo', exception['message'])
        self.assertEqual('test_notify_exception_with_traceback_option',
                         stacktrace[0]['method'])

    def test_notify_exception_tuple_with_traceback(self):

        def send_notify():
            backtrace = None
            try:
                raise ScaryException('foo')
            except ScaryException:
                backtrace = sys.exc_info()[2]
            bugsnag.notify((Exception, Exception("foo"), backtrace))

        send_notify()
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        stacktrace = exception['stacktrace']
        self.assertEqual(1, len(self.server.events_received))
        self.assertEqual('foo', exception['message'])
        self.assertEqual('send_notify',
                         stacktrace[0]['method'])

    def test_notify_exception_tuple(self):
        bugsnag.notify((Exception, Exception("foo"), None))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual(1, len(self.server.events_received))
        self.assertEqual("RuntimeError", exception['errorClass'])

    def test_notify_metadata_set_value(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       value=set([6, "cow", "gravy"]))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        value = event['metaData']['custom']['value']
        self.assertEqual(3, len(value))
        self.assertTrue(6 in value)
        self.assertTrue("cow" in value)
        self.assertTrue("gravy" in value)

    def test_notify_metadata_tuple_value(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       value=(3, "cow", "gravy"))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual([3, "cow", "gravy"],
                         event['metaData']['custom']['value'])

    def test_notify_metadata_integer_value(self):
        bugsnag.notify(ScaryException('unexpected failover'),
                       value=5, value2=-13)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual(5, event['metaData']['custom']['value'])
        self.assertEqual(-13, event['metaData']['custom']['value2'])

    def test_notify_error_message(self):
        bugsnag.notify(ScaryException('unexpécted failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        exception = event['exceptions'][0]
        self.assertEqual('unexpécted failover', exception['message'])

    def test_notify_unicode_metadata(self):
        bins = ('\x98\x00\x00\x00\t\x81\x19\x1b\x00\x00\x00\x00\xd4\x07\x00'
                '\x00\x00\x00\x00\x00R\x00\x00\x00\x00\x00\xff\xff\xff\xffe'
                '\x00\x00\x00\x02project\x00%\x00\x00\x00f65f051b-d762-5983'
                '-838b-a05aadc06a5\x00\x02uid\x00%\x00\x00\x001bab969f-7b30'
                '-459a-adee-917b9e028eed\x00\x00')
        self_class = 'tests.test_notify.TestBugsnag'
        bugsnag.notify(Exception('free food'), metadata={'payload': {
            'project': '∆πåß∂ƒ',
            'filename': 'DISPOSITIFS DE SÉCURITÉ.pdf',
            '♥♥i': '♥♥♥♥♥♥',
            'src_name': '☻☻☻☻☻ RDC DISPOSITIFS DE SÉCURTÉ.pdf',
            'accénted': '☘☘☘éééé@me.com',
            'class': self.__class__,
            'another_class': dict,
            'self': self,
            'var': bins
        }})
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertEqual('∆πåß∂ƒ', event['metaData']['payload']['project'])
        self.assertEqual('♥♥♥♥♥♥',
                         event['metaData']['payload']['♥♥i'])
        self.assertEqual('DISPOSITIFS DE SÉCURITÉ.pdf',
                         event['metaData']['payload']['filename'])
        self.assertEqual('☻☻☻☻☻ RDC DISPOSITIFS DE SÉCURTÉ.pdf',
                         event['metaData']['payload']['src_name'])
        self.assertEqual('☘☘☘éééé@me.com',
                         event['metaData']['payload']['accénted'])
        self.assertEqual(bins, event['metaData']['payload']['var'])
        self.assertEqual("<class 'tests.test_notify.TestBugsnag'>",
                         event['metaData']['payload']['class'])

        if sys.version_info < (3, 11):
            assert event['metaData']['payload']['self'] == \
                'test_notify_unicode_metadata (%s)' % self_class
        else:
            method = 'test_notify_unicode_metadata'

            assert event['metaData']['payload']['self'] == \
                'test_notify_unicode_metadata (%s.%s)' % (self_class, method)

    def test_notify_stacktrace(self):
        samples.call_bugsnag_nested()
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        frames = event['exceptions'][0]['stacktrace']

        self.assertTrue(frames[0]['file'].endswith('fixtures/samples.py'))
        self.assertEqual(11, frames[0]['lineNumber'])
        self.assertEqual('chain_3', frames[0]['method'])
        self.assertEqual('chain_3', frames[0]['method'])
        self.assertEqual('', frames[0]['code']['7'])
        self.assertEqual('', frames[0]['code']['8'])
        self.assertEqual('def chain_3():', frames[0]['code']['9'])
        self.assertEqual('    import bugsnag', frames[0]['code']['10'])
        self.assertEqual("    bugsnag.notify(Exception('oh noooo'))",
                         frames[0]['code']['11'])

        self.assertTrue(frames[1]['file'].endswith('fixtures/samples.py'))
        self.assertEqual(6, frames[1]['lineNumber'])
        self.assertEqual('chain_2', frames[1]['method'])
        self.assertEqual('', frames[1]['code']['4'])
        self.assertEqual('def chain_2():', frames[1]['code']['5'])
        self.assertEqual('    chain_3()', frames[1]['code']['6'])
        self.assertEqual('', frames[1]['code']['7'])
        self.assertEqual('', frames[1]['code']['8'])

        self.assertTrue(frames[2]['file'].endswith('fixtures/samples.py'))
        self.assertEqual(2, frames[2]['lineNumber'])
        self.assertEqual('def call_bugsnag_nested():', frames[2]['code']['1'])
        self.assertEqual('    chain_2()', frames[2]['code']['2'])
        self.assertEqual('', frames[2]['code']['3'])
        self.assertEqual('', frames[2]['code']['4'])

    def test_notify_proxy(self):
        bugsnag.configure(proxy_host='http://' + self.server.address)
        bugsnag.notify(ScaryException('unexpected failover'))

        assert self.sent_report_count == 1
        assert self.server.events_received[0]['method'] == 'POST'
        assert self.server.events_received[0]['path'] == self.server.events_url

    def test_notify_unhandled_defaults(self):
        bugsnag.notify(ScaryException("unexpected failover"))

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            "type": "handledException"
        })

    def test_notify_severity_overridden(self):
        bugsnag.notify(ScaryException("unexpected failover"), severity="info")

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            "type": "userSpecifiedSeverity"
        })

    def test_notify_unhandled_severity_callback(self):
        def callback(report):
            report.severity = "info"

        bugsnag.before_notify(callback)

        bugsnag.notify(ScaryException("unexpected failover"), severity="error")

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severityReason'], {
            "type": "userCallbackSetSeverity"
        })

    def test_middleware_stack_order_legacy(self):
        def first_callback(event):
            event.metadata['test']['array'].append(1)

        def second_callback(event):
            event.metadata['test']['array'].append(2)

        # Add a regular callback function
        bugsnag.before_notify(second_callback)

        # Simulate an internal middleware
        bugsnag.legacy.configuration.internal_middleware.before_notify(
                first_callback)

        bugsnag.notify(ScaryException('unexpected failover'),
                       test={'array': []})
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        self.assertEqual(event['metaData']['test']['array'], [1, 2])

    def test_middleware_stack_order(self):
        client = bugsnag.Client(
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            api_key='tomatoes',
            notify_release_stages=['dev'],
            release_stage='dev',
            asynchronous=False,
        )

        def first_callback(event):
            event.metadata['test']['array'].append(1)

        def second_callback(event):
            event.metadata['test']['array'].append(2)

        client.configuration.middleware.before_notify(second_callback)
        client.configuration.internal_middleware.before_notify(first_callback)

        client.notify(ScaryException('unexpected failover'),
                      test={'array': []})
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        self.assertEqual(event['metaData']['test']['array'], [1, 2])

    def test_internal_middleware_changes_severity(self):
        client = bugsnag.Client(
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            api_key='tomatoes',
            notify_release_stages=['dev'],
            release_stage='dev',
            asynchronous=False,
        )

        def severity_callback(event):
            event.severity = 'info'

        internal_middleware = client.configuration.internal_middleware
        internal_middleware.before_notify(severity_callback)

        client.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        self.assertEqual(event['severity'], 'info')
        self.assertEqual(event['severityReason']['type'], 'handledException')

    def test_internal_middleware_can_change_severity_reason(self):
        client = bugsnag.Client(
            endpoint=self.server.events_url,
            session_endpoint=self.server.sessions_url,
            api_key='tomatoes',
            notify_release_stages=['dev'],
            release_stage='dev',
            asynchronous=False,
        )

        def severity_reason_callback(event):
            event.severity_reason['type'] = 'testReason'

        internal_middleware = client.configuration.internal_middleware
        internal_middleware.before_notify(severity_reason_callback)

        client.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        self.assertEqual(event['severityReason']['type'], 'testReason')

    def test_external_middleware_can_change_severity(self):

        def severity_callback(event):
            event.severity = 'info'

        bugsnag.before_notify(severity_callback)

        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        self.assertEqual(event['severity'], 'info')
        self.assertEqual(event['severityReason']['type'],
                         'userCallbackSetSeverity')

    def test_external_middleware_cannot_change_severity_reason(self):

        def severity_reason_callback(event):
            event.severity_reason['type'] = 'testReason'

        bugsnag.before_notify(severity_reason_callback)

        bugsnag.notify(ScaryException('unexpected failover'))
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]

        self.assertEqual(event['severityReason']['type'], 'handledException')

    def test_auto_notify_defaults(self):
        bugsnag.auto_notify(ScaryException("unexpected failover"))

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue(event['unhandled'])
        self.assertEqual(event['severity'], 'error')
        self.assertEqual(event['severityReason'], {
            "type": "unhandledException"
        })

    def test_auto_notify_overrides(self):
        bugsnag.auto_notify(
            ScaryException("unexpected failover"),
            severity='info',
            unhandled=False,
            severity_reason={
                "type": "middleware_handler",
                "attributes": {
                    "name": "test middleware"
                }
            }
        )

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severity'], 'info')
        self.assertEqual(event['severityReason'], {
            "type": "middleware_handler",
            "attributes": {
                "name": "test middleware"
            }
        })

    def test_auto_notify_ignored_exc_info(self):
        bugsnag.configure(auto_notify=False)
        try:
            raise ScaryException('Testing Notify EXC Info')
        except Exception:
            bugsnag.auto_notify_exc_info()

        self.assertEqual(len(self.server.events_received), 0)

    def test_auto_notify_exc_info(self):
        try:
            raise ScaryException('Testing Notify EXC Info')
        except Exception:
            bugsnag.auto_notify_exc_info()

        self.assertEqual(len(self.server.events_received), 1)
        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertTrue(event['unhandled'])
        self.assertEqual(event['severity'], 'error')
        self.assertEqual(event['severityReason'], {
            "type": "unhandledException"
        })
        self.assertEqual(event['exceptions'][0]['message'],
                         'Testing Notify EXC Info')

    def test_auto_notify_exc_info_overrides(self):
        try:
            raise ScaryException('Testing Notify EXC Info')
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            replacement = Exception(str(exc_value))
            bugsnag.auto_notify_exc_info(
                ('Exception', replacement, exc_tb),
                severity='info',
                unhandled=False,
                severity_reason={
                    "type": "middleware_handler",
                    "attributes": {
                        "name": "test middleware"
                    }
                }
            )

        json_body = self.server.events_received[0]['json_body']
        event = json_body['events'][0]
        self.assertFalse(event['unhandled'])
        self.assertEqual(event['severity'], 'info')
        self.assertEqual(event['severityReason'], {
            "type": "middleware_handler",
            "attributes": {
                "name": "test middleware"
            }
        })
        self.assertEqual(event['exceptions'][0]['errorClass'], 'Exception')
        self.assertEqual(event['exceptions'][0]['message'],
                         'Testing Notify EXC Info')

    def test_synchronous_individual_notify(self):
        bugsnag.configure(asynchronous=True)
        bugsnag.notify(ScaryException('unexpected failover'),
                       asynchronous=False)
        assert len(self.server.events_received) == 1

    def test_meta_data_warning(self):
        with pytest.warns(DeprecationWarning) as records:
            bugsnag.notify(ScaryException('false equivalence'),
                           meta_data={'fruit': {'apples': 2}})

            assert len(records) == 1
            assert str(records[0].message) == ('The Event "meta_data" ' +
                                               'argument has been replaced ' +
                                               'with "metadata"')

        json_body = self.server.events_received[0]['json_body']
        metadata = json_body['events'][0]['metaData']
        assert metadata['fruit']['apples'] == 2
