import unittest
import json

from six import u
from bugsnag.utils import SanitizingJSONEncoder, FilterDict


class TestUtils(unittest.TestCase):

    def test_encode_filters(self):
        data = FilterDict({"credit_card": "123213213123", "password": "456",
                           "cake": True})
        encoder = SanitizingJSONEncoder(keyword_filters=["credit_card",
                                                         "password"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"credit_card": "[FILTERED]",
                                     "password": "[FILTERED]",
                                     "cake": True})

    def test_sanitize_list(self):
        data = FilterDict({"list": ["carrots", "apples", "peas"],
                           "passwords": ["abc", "def"]})
        encoder = SanitizingJSONEncoder(keyword_filters=["credit_card",
                                                         "passwords"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"list": ["carrots", "apples", "peas"],
                                     "passwords": "[FILTERED]"})

    def test_sanitize_valid_unicode_object(self):
        data = {"item": u('\U0001f62c')}
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, data)

    def test_sanitize_nested_object_filters(self):
        data = FilterDict({"metadata": {"another_password": "My password"}})
        encoder = SanitizingJSONEncoder(keyword_filters=["password"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"metadata": {"another_password": "[FILTERED]"}})

    def test_sanitize_bad_utf8_object(self):
        data = {"bad_utf8": u("test \xe9")}
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, data)

    def test_sanitize_unencoded_object(self):
        data = {"exc": Exception()}
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"exc": ""})

    def test_json_encode(self):
        payload = {"a": u("a") * 512 * 1024}
        expected = {"a": u("a") * 1024}
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        self.assertEqual(json.loads(encoder.encode(payload)), expected)

    def test_filter_dict(self):
        data = FilterDict({"metadata": {"another_password": "My password"}})
        encoder = SanitizingJSONEncoder(keyword_filters=["password"])
        sane_data = encoder.filter_string_values(data)
        self.assertEqual(sane_data,
                         {"metadata": {"another_password": "[FILTERED]"}})

    def test_unfiltered_encode(self):
        data = {"metadata": {"another_password": "My password"}}
        encoder = SanitizingJSONEncoder(keyword_filters=["password"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, data)
