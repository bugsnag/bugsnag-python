import os
import socket
import unittest

from bugsnag.configuration import Configuration


class TestConfiguration(unittest.TestCase):

    def test_get_endpoint(self):
        # Test default endpoint with ssl
        c = Configuration()
        c.use_ssl = True
        self.assertEqual(c.get_endpoint(), "https://notify.bugsnag.com")

        # Test default endpoint without ssl
        c = Configuration()
        c.use_ssl = False
        self.assertEqual(c.get_endpoint(), "http://notify.bugsnag.com")

        # Test custom endpoint
        c = Configuration()
        c.use_ssl = False
        c.endpoint = "localhost:1234"
        self.assertEqual(c.get_endpoint(), "http://localhost:1234")

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
