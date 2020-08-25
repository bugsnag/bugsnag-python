import os
import socket
import unittest

from bugsnag.configuration import Configuration
from bugsnag.middleware import DefaultMiddleware
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

    def test_ignore_classes(self):
        # Test ignoring a class works
        c = Configuration()
        c.ignore_classes.append("SystemError")
        self.assertTrue(c.should_ignore(SystemError("Example")))

        c = Configuration()
        c.ignore_classes.append("SystemError")
        self.assertFalse(c.should_ignore(Exception("Example")))

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
        self.assertEqual(c.internal_middleware.stack,
                         [DefaultMiddleware, SessionMiddleware])
        self.assertEqual(len(c.middleware.stack), 0)

    def test_validate_api_key(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(api_key=[])

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'api_key should be str, got list. ' +
                    'This will be an error in a future release.')
            c.configure(api_key='ffff')

            assert len(record) == 1
            assert c.api_key == 'ffff'

    def test_validate_endpoint(self):
        c = Configuration()
        with pytest.warns(RuntimeWarning) as record:
            c.configure(endpoint=56)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'endpoint should be str, got int. ' +
                    'This will be an error in a future release.')
            assert c.endpoint == 'https://notify.bugsnag.com'

            c.configure(endpoint='https://notify.example.com')

            assert len(record) == 1
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
        with pytest.warns(RuntimeWarning) as record:
            c.configure(project_root=True)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'project_root should be str, got bool')
            assert c.project_root == os.getcwd()

            c.configure(project_root='/path/to/python/project')

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
        with pytest.warns(RuntimeWarning) as record:
            c.configure(session_endpoint=False)

            assert len(record) == 1
            assert (str(record[0].message) ==
                    'session_endpoint should be str, got bool. This will be' +
                    ' an error in a future release.')
            assert c.session_endpoint == 'https://sessions.bugsnag.com'

            c.configure(session_endpoint='https://sessions.example.com')

            assert len(record) == 1
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
        with pytest.warns(RuntimeWarning) as record:
            c.configure(emperor=True)
            assert len(record) == 1
            assert (str(record[0].message) ==
                    'received unknown configuration option "emperor"')
