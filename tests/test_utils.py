import unittest

from nose.tools import eq_

from six import u
from bugsnag.utils import json_encode, sanitize_object


class TestUtils(unittest.TestCase):

    def test_sanitize_filters(self):
        data = {"credit_card": "123213213123", "password": "456", "cake": True}
        sane_data = sanitize_object(data, filters=["credit_card", "password"])
        eq_(sane_data, {"credit_card": "[FILTERED]",
                        "password": "[FILTERED]",
                        "cake": True})

    def test_sanitize_list(self):
        data = {"list": ["carrots", "apples", "peas"],
                "passwords": ["abc", "def"]}
        sane_data = sanitize_object(data, filters=["credit_card", "password"])
        eq_(sane_data, {"list": ["carrots", "apples", "peas"],
                        "passwords": "[FILTERED]"})

    def test_sanitize_valid_unicode_object(self):
        data = {"item": u('\U0001f62c')}
        sane_data = sanitize_object(data, filters=[])
        eq_(sane_data, data)

    def test_sanitize_nested_object_filters(self):
        data = {"metadata": {"another_password": "My password"}}
        sane_data = sanitize_object(data, filters=["password"])
        eq_(sane_data, {"metadata": {"another_password": "[FILTERED]"}})

    def test_sanitize_bad_utf8_object(self):
        data = {"bad_utf8": u("test \xe9")}
        sane_data = sanitize_object(data, filters=[])
        eq_(sane_data, data)

    def test_sanitize_unencoded_object(self):
        data = {"exc": Exception()}
        sane_data = sanitize_object(data, filters=[])
        eq_(sane_data, {"exc": ""})

    def test_json_encode(self):
        payload = {"a": u("a") * 512 * 1024}
        eq_(json_encode(payload),
            ('{"a": "' + 'a' * 1024 + '"}').encode('utf-8', 'replace'))
