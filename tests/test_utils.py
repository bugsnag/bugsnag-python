import unittest

from nose.tools import eq_

from six import u
from bugsnag.utils import json_encode, sanitize_object


class TestUtils(unittest.TestCase):

    def test_sanitize_object(self):
        filters = ["password", "credit_card"]
        crazy_dict = {
            "password": "123456",
            "metadata": {
                "another_password": "123456",
                "regular": "text"
            },
            "bad_utf8": "a test of \xe9 char",
            "list": ["list", "of", "things"],
            "unicode": u("string"),
            "obj": Exception(),
            "valid_unicode": u("\u2603"),
        }

        # Sanitize our object
        sane_dict = sanitize_object(crazy_dict, filters=filters)

        # Check the values have been sanitized
        eq_(sane_dict["password"], "[FILTERED]")
        eq_(sane_dict["metadata"]["another_password"], "[FILTERED]")
        eq_(sane_dict["metadata"]["regular"], "text")
        self.assertTrue("things" in sane_dict["list"])

    def test_json_encode(self):
        payload = {"a": u("a") * 512 * 1024}
        eq_(json_encode(payload),
            ('{"a": "' + 'a' * 1024 + '"}').encode('utf-8', 'replace'))
