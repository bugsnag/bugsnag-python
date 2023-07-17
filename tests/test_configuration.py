import os
import socket
import logging
import random
import sys
import time
import unittest
from pathlib import PurePath, Path
from unittest.mock import patch
from io import StringIO
from threading import Thread

from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.configuration import Configuration
from bugsnag.error import Error
from bugsnag.middleware import DefaultMiddleware, SimpleMiddleware
from bugsnag.sessiontracker import SessionMiddleware

import pytest


class TestConfiguration(unittest.TestCase):

    def test_reads_api_key_from_environ(self):
        os.environ['BUGSNAG_API_KEY'] = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        c = Configuration()
        self.assertEqual(c.api_key, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        self.assertEqual(c.project_root, os.getcwd())

    def test_should_notify(self):
        # Test custom release_stage
        c = Configuration()
        c.release_stage = "anything"
        self.assertTrue(c.should_notify())

        # Test release_stage in notify_release_stages
        c = Configuration()
        c.notify_release_stages = ["production"]
        c.release_stage = "development"
        self.assertFalse(c.should_notify())

        # Test release_stage in notify_release_stages
        c = Configuration()
        c.notify_release_stages = ["custom"]
        c.release_stage = "custom"
        self.assertTrue(c.should_notify())

    def test_ignore_classes_with_a_single_exception(self):
        # Test ignoring a class works with a single Exception
        c = Configuration()
        c.ignore_classes.append("SystemError")
        self.assertTrue(c.should_ignore(SystemError("Example")))

        c = Configuration()
        c.ignore_classes.append("SystemError")
        self.assertFalse(c.should_ignore(Exception("Example")))

    def test_ignore_classes_works_with_list_of_errors(self):
        # Test ignoring a class works with a list of Errors
        c = Configuration()
        c.ignore_classes.append("SystemError")

        error1 = Error('SystemError', 'ahh', [])
        error2 = Error('AnotherError', 'ahh', [])
        error3 = Error('SomeOtherError', 'ahh', [])
        error4 = Error('Exception', 'ahh', [])

        assert c.should_ignore([error1, error2, error3, error4])
        assert c.should_ignore([error4, error3, error2, error1])
        assert c.should_ignore([error1])

        assert not c.should_ignore([error2, error3, error4])
        assert not c.should_ignore([error4, error3, error2])

    def test_hostname(self):
        c = Configuration()
        self.assertEqual(c.hostname, socket.gethostname())

        os.environ["DYNO"] = "YES"
        c = Configuration()
        self.assertEqual(c.hostname, None)

    def test_session_tracking_defaults(self):
        c = Configuration()
        self.assertTrue(c.auto_capture_sessions)
        self.assertEqual(c.session_endpoint, "https://sessions.bugsnag.com")

    def test_default_middleware_location(self):
        c = Configuration()

        assert len(c.internal_middleware.stack) == 3
        assert isinstance(c.internal_middleware.stack[0], SimpleMiddleware)
        assert c.internal_middleware.stack[1] is DefaultMiddleware
        assert c.internal_middleware.stack[2] is SessionMiddleware

        assert len(c.middleware.stack) == 0

    def test_validate_api_key(self):
        c = Configuration()
        with pytest.raises(TypeError) as e:
            c.configure(api_key=[])
            assert str(e) == 'api_key should be str, got list.'
        c.configure(api_key='ffff')
        assert c.api_key == 'ffff'

    def test_validate_endpoint(self):
        c = Configuration()
        with pytest.raises(TypeError) as e:
            c.configure(endpoint=56)

            assert str(e) == 'endpoint should be str, got int. '
            assert c.endpoint == 'https://notify.bugsnag.com'

        c.configure(endpoint='https://notify.example.com')
        assert c.endpoint == 'https://notify.example.com'

    def test_validate_app_type(self):
        c = Configuration()
        assert c.app_type is None
        with pytest.warns(RuntimeWarning) as record:
            c.configure(app_type=[])

            assert len(record) == 1
            assert str(record[0].message) == 'app_type should be str, got list'
            assert c.app_type is None

            c.configure(app_type='rq')

            assert len(record) == 1
            assert c.app_type == 'rq'

    def test_validate_app_version(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(app_version=[])

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'app_version should be str, got list')
            assert c.app_version is None

            c.configure(app_version='1.2.6')

            assert len(record) == 1
            assert c.app_version == '1.2.6'

    def test_validate_asynchronous(self):
        c = Configuration()
        assert c.asynchronous is True
        with pytest.warns(RuntimeWarning) as record:
            c.configure(asynchronous='true')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'asynchronous should be bool, got str')
            assert c.asynchronous is True

            c.configure(asynchronous=False)
            assert len(record) == 1
            assert c.asynchronous is False

    def test_validate_auto_notify(self):
        c = Configuration()
        assert c.auto_notify is True
        with pytest.warns(RuntimeWarning) as record:
            c.configure(auto_notify='true')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'auto_notify should be bool, got str')

            c.configure(auto_notify=False)
            assert len(record) == 1
            assert c.auto_notify is False

    def test_validate_auto_capture_sessions(self):
        c = Configuration()
        assert c.auto_capture_sessions is True
        with pytest.warns(RuntimeWarning) as record:
            c.configure(auto_capture_sessions='true')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'auto_capture_sessions should be bool, got str')

            c.configure(auto_capture_sessions=False)
            assert len(record) == 1
            assert c.auto_capture_sessions is False

    def test_validate_delivery(self):
        c = Configuration()
        assert c.delivery is not None

        class BadDelivery(object):
            def deliv(self, *args, **kwargs):
                pass

        class GoodDelivery(object):
            def deliver(self, *args, **kwargs):
                pass

        with pytest.warns(RuntimeWarning) as record:
            c.configure(delivery=BadDelivery())

            assert len(record) == 1
            assert (str(record[0].message) ==
                    ('delivery should implement Delivery interface, ' +
                     'got BadDelivery. This will be an error in a future ' +
                     'release.'))

            good = GoodDelivery()
            c.configure(delivery=good)
            assert len(record) == 1
            assert c.delivery == good

    def test_validate_hostname(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(hostname=[])

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'hostname should be str, got list')
            assert c.hostname is None

            c.configure(hostname='testserver')

            assert len(record) == 1
            assert c.hostname == 'testserver'

    def test_validate_ignore_classes(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(ignore_classes=302)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'ignore_classes should be list or tuple, got int')
            assert isinstance(c.ignore_classes, (list, tuple))

            c.configure(ignore_classes=['LookupError'])

            assert len(record) == 1
            assert c.ignore_classes == ['LookupError']

    def test_validate_lib_root(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(lib_root=False)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'lib_root should be str, got bool')

            c.configure(lib_root='/path/to/python/lib')

            assert len(record) == 1
            assert c.lib_root == '/path/to/python/lib'

    def test_validate_notify_release_stages(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(notify_release_stages='beta')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'notify_release_stages should be list or tuple, got str')
            assert c.notify_release_stages is None

            c.configure(notify_release_stages=['beta'])

            assert len(record) == 1
            assert c.notify_release_stages == ['beta']

    def test_validate_params_filters(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(params_filters='pw')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'params_filters should be list or tuple, got str')
            assert isinstance(c.params_filters, list)

            c.configure(params_filters=['pw'])

            assert len(record) == 1
            assert c.params_filters == ['pw']

    def test_validate_project_root(self):
        c = Configuration()

        if sys.version_info < (3, 6):
            expected_type = 'PurePath'
        else:
            expected_type = 'PathLike'

        with pytest.warns(RuntimeWarning) as record:
            c.configure(project_root=True)

            assert len(record) == 1
            assert str(record[0].message) == \
                'project_root should be str or %s, got bool' % expected_type
            assert c.project_root == os.getcwd()

            c.configure(project_root='/path/to/python/project')

            assert len(record) == 1
            assert c.project_root == '/path/to/python/project'

            c.configure(project_root=Path('/path/to/python/project'))

            assert len(record) == 1
            assert c.project_root == '/path/to/python/project'

            c.configure(project_root=PurePath('/path/to/python/project'))

            assert len(record) == 1
            assert c.project_root == '/path/to/python/project'

    def test_validate_proxy_host(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(proxy_host=True)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'proxy_host should be str, got bool')
            assert c.proxy_host is None

            c.configure(proxy_host='112.0.0.45')

            assert len(record) == 1
            assert c.proxy_host == '112.0.0.45'

    def test_validate_release_stage(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(release_stage=False)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'release_stage should be str, got bool')
            assert c.release_stage == 'production'

            c.configure(release_stage='beta-2')

            assert len(record) == 1
            assert c.release_stage == 'beta-2'

    def test_validate_send_code(self):
        c = Configuration()
        assert c.send_code is True
        with pytest.warns(RuntimeWarning) as record:
            c.configure(send_code='false')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'send_code should be bool, got str')
            assert c.send_code is True

            c.configure(send_code=False)
            assert len(record) == 1
            assert c.send_code is False

    def test_validate_send_environment(self):
        c = Configuration()
        assert c.send_environment is False
        with pytest.warns(RuntimeWarning) as record:
            c.configure(send_environment='True')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'send_environment should be bool, got str')
            assert c.send_environment is False

            c.configure(send_environment=True)
            assert len(record) == 1
            assert c.send_environment is True

    def test_validate_session_endpoint(self):
        c = Configuration()
        with pytest.raises(TypeError) as e:
            c.configure(session_endpoint=False)

            assert str(e) == 'session_endpoint should be str, got bool.'
            assert c.session_endpoint == 'https://sessions.bugsnag.com'

        c.configure(session_endpoint='https://sessions.example.com')
        assert c.session_endpoint == 'https://sessions.example.com'

    def test_validate_traceback_exclude_modules(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(traceback_exclude_modules='_.logger')

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'traceback_exclude_modules should be list or tuple, ' +
                    'got str')
            assert isinstance(c.traceback_exclude_modules, list)

            c.configure(traceback_exclude_modules=['_.logger'])

            assert len(record) == 1
            assert c.traceback_exclude_modules == ['_.logger']

    def test_validate_unknown_config_option(self):
        c = Configuration()
        with pytest.raises(TypeError):
            c.configure(emperor=True)

    @patch('sys.stderr', new_callable=StringIO)
    def test_default_logger(self, mock_stderr):
        config = Configuration()

        assert isinstance(config.logger, logging.Logger)

        # debug and info calls should be ignored by default
        config.logger.debug('hello debug!')
        config.logger.info('hello info!')
        assert mock_stderr.getvalue() == ''

        config.logger.warning('hello warning!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] WARNING - hello warning!\n'
        )

        config.logger.error('hello error!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] ERROR - hello error!\n'
        )

        config.logger.critical('hello critical!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] CRITICAL - hello critical!\n'
        )

        config.logger.exception('hello exception! %s', Exception('oh no!'))
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] ERROR - hello exception! oh no!\nNoneType: None\n'
        )

    @patch('sys.stderr', new_callable=StringIO)
    def test_default_logger_with_configure_call(self, mock_stderr):
        config = Configuration()
        config.configure(app_type='very good')

        assert isinstance(config.logger, logging.Logger)

        # debug and info calls should be ignored by default
        config.logger.debug('hello debug!')
        config.logger.info('hello info!')
        assert mock_stderr.getvalue() == ''

        config.logger.warning('hello warning!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] WARNING - hello warning!\n'
        )

        config.logger.error('hello error!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] ERROR - hello error!\n'
        )

        config.logger.critical('hello critical!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] CRITICAL - hello critical!\n'
        )

        config.logger.exception('hello exception! %s', Exception('oh no!'))
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] ERROR - hello exception! oh no!\nNoneType: None\n'
        )

    @patch('sys.stderr', new_callable=StringIO)
    def test_logger_can_be_disabled(self, mock_stderr):
        config = Configuration(logger=None)

        assert isinstance(config.logger, logging.Logger)

        config.logger.debug('hello debug!')
        config.logger.info('hello info!')
        config.logger.warning('hello warning!')
        config.logger.error('hello error!')
        config.logger.critical('hello critical!')
        config.logger.exception('hello exception!')

        assert mock_stderr.getvalue() == ''

    @patch('sys.stderr', new_callable=StringIO)
    def test_logger_can_be_disabled_using_configure(self, mock_stderr):
        config = Configuration()
        config.configure(logger=None)

        assert isinstance(config.logger, logging.Logger)

        config.logger.debug('hello debug!')
        config.logger.info('hello info!')
        config.logger.warning('hello warning!')
        config.logger.error('hello error!')
        config.logger.critical('hello critical!')
        config.logger.exception('hello exception!')

        assert mock_stderr.getvalue() == ''

    @patch('sys.stderr', new_callable=StringIO)
    def test_default_logger_is_used_if_invalid_logger_set(self, mock_stderr):
        with pytest.warns(RuntimeWarning) as warnings:
            config = Configuration(logger=123)

        expected_message = 'logger should be logging.Logger, got int'

        assert len(warnings) == 1
        assert warnings[0].message.args[0] == expected_message

        # the default logger should be used
        assert isinstance(config.logger, logging.Logger)

        config.logger.warning('hello warning!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] WARNING - hello warning!\n'
        )

    @patch('sys.stderr', new_callable=StringIO)
    def test_default_logger_is_used_if_invalid_logger_set_with_configure(
        self,
        mock_stderr
    ):
        config = Configuration()

        with pytest.warns(RuntimeWarning) as warnings:
            config.configure(logger='hello')

        expected_message = 'logger should be logging.Logger, got str'

        assert len(warnings) == 1
        assert warnings[0].message.args[0] == expected_message

        # the default logger should be used
        assert isinstance(config.logger, logging.Logger)

        config.logger.warning('hello warning!')
        assert mock_stderr.getvalue().endswith(
            '[bugsnag] WARNING - hello warning!\n'
        )

    def test_validate_max_breadcrumbs_type(self):
        c = Configuration()

        with pytest.warns(RuntimeWarning) as record:
            c.configure(max_breadcrumbs='one million')

            assert len(record) == 1

            message = str(record[0].message)
            assert message == 'max_breadcrumbs should be int, got str'
            assert c.max_breadcrumbs == 25

        c.configure(max_breadcrumbs=12)
        assert c.max_breadcrumbs == 12

    def test_validate_max_breadcrumbs_less_than_0(self):
        c = Configuration()

        with pytest.warns(RuntimeWarning) as record:
            c.configure(max_breadcrumbs=-1)

            assert len(record) == 1

            message = str(record[0].message)
            assert message == 'max_breadcrumbs should be an int between 0 ' \
                'and 100, got "-1"'
            assert c.max_breadcrumbs == 25

        c.configure(max_breadcrumbs=0)
        assert c.max_breadcrumbs == 0

    def test_validate_max_breadcrumbs_greater_than_100(self):
        c = Configuration()

        with pytest.warns(RuntimeWarning) as record:
            c.configure(max_breadcrumbs=101)

            assert len(record) == 1

            message = str(record[0].message)
            assert message == 'max_breadcrumbs should be an int between 0 ' \
                'and 100, got "101"'
            assert c.max_breadcrumbs == 25

        c.configure(max_breadcrumbs=100)
        assert c.max_breadcrumbs == 100

    def test_breadcrumb_log_level(self):
        c = Configuration()
        assert c.breadcrumb_log_level == logging.INFO

        c.configure(breadcrumb_log_level=logging.ERROR)
        assert c.breadcrumb_log_level == logging.ERROR

    def test_enabled_breadcrumb_types(self):
        c = Configuration()
        assert c.enabled_breadcrumb_types == list(BreadcrumbType)

        c.configure(enabled_breadcrumb_types=[BreadcrumbType.ERROR])
        assert c.enabled_breadcrumb_types == [BreadcrumbType.ERROR]

    def test_breadcrumbs_are_read_only(self):
        c = Configuration()
        assert c.breadcrumbs == []

        c.breadcrumbs.append('definitely a breadcrumb')
        assert c.breadcrumbs == []

        with pytest.raises(AttributeError) as e:
            c.breadcrumbs = ['??']

            assert str(e) == "AttributeError: can't set attribute"

    def test_on_breadcrumb_callbacks_can_be_added_and_removed(self):
        c = Configuration()
        assert c._on_breadcrumbs == []

        def on_breadcrumb():
            pass

        on_breadcrumb_2 = lambda: None  # noqa: E731

        c.add_on_breadcrumb(on_breadcrumb)
        assert c._on_breadcrumbs == [on_breadcrumb]

        c.add_on_breadcrumb(on_breadcrumb_2)
        assert c._on_breadcrumbs == [on_breadcrumb, on_breadcrumb_2]

        c.remove_on_breadcrumb(on_breadcrumb)
        assert c._on_breadcrumbs == [on_breadcrumb_2]

        c.remove_on_breadcrumb(on_breadcrumb_2)
        assert c._on_breadcrumbs == []

    def test_removing_a_nonexistent_on_breadcrumb_callback_does_nothing(self):
        c = Configuration()

        c.remove_on_breadcrumb(lambda: None)
        assert c._on_breadcrumbs == []

    def test_concurrent_access_to_on_breadcrumb_callbacks(self):
        c = Configuration()

        def first_on_breadcrumb():
            pass

        def second_on_breadcrumb():
            pass

        def add_callbacks():
            try:
                thread.exception = None

                c.add_on_breadcrumb(first_on_breadcrumb)

                # sleep for a bit to allow other threads time to interfere
                time.sleep(random.randrange(0, 100) / 1000)

                c.remove_on_breadcrumb(first_on_breadcrumb)
                c.add_on_breadcrumb(first_on_breadcrumb)

                # sleep for a bit to allow other threads time to interfere
                time.sleep(random.randrange(0, 100) / 1000)

                c.add_on_breadcrumb(second_on_breadcrumb)

                # sleep for a bit to allow other threads time to interfere
                time.sleep(random.randrange(0, 100) / 1000)

                c.remove_on_breadcrumb(second_on_breadcrumb)
                c.add_on_breadcrumb(second_on_breadcrumb)

            except Exception as e:
                thread.exception = e

        number_of_threads = 5

        threads = []
        for i in range(number_of_threads):
            thread = Thread(target=add_callbacks)
            threads.append(thread)

        # shuffle the list of threads so they don't run in a reliable order
        random.shuffle(threads)

        for thread in threads:
            thread.start()

        # shuffle the list of threads so they don't run in a reliable order
        random.shuffle(threads)

        for thread in threads:
            thread.join(2)

            assert not thread.is_alive()

            # if an exception happened in the thread, raise it here instead
            if thread.exception is not None:
                raise thread.exception

        assert len(c._on_breadcrumbs) == number_of_threads * 2
