import unittest
import json
import timeit
import sys

from six import u
from bugsnag.utils import SanitizingJSONEncoder, FilterDict, ThreadLocals


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

    def test_thread_locals(self):
        key = "TEST_THREAD_LOCALS"
        val = {"Test": "Thread", "Locals": "Here"}
        locs = ThreadLocals.get_instance()
        self.assertFalse(locs.has_item(key))
        locs.set_item(key, val)
        self.assertTrue(locs.has_item(key))
        item = locs.get_item(key)
        self.assertEqual(item, val)
        locs.del_item(key)
        self.assertFalse(locs.has_item(key))
        item = locs.get_item(key, "default")
        self.assertEqual(item, "default")

    def test_encoding_recursive(self):
        """
        Test that recursive data structures are replaced with '[RECURSIVE]'
        """
        data = {"Test": ["a", "b", "c"]}
        data["Self"] = data
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a", "b", "c"], "Self": "[RECURSIVE]"})

    def test_encoding_recursive_repeated(self):
        """
        Test that encoding the same object twice produces the same result
        """
        data = {"Test": ["a", "b", "c"]}
        data["Self"] = data
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a", "b", "c"], "Self": "[RECURSIVE]"})
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a", "b", "c"], "Self": "[RECURSIVE]"})

    def test_encoding_nested_repeated(self):
        """
        Test that encoding the same object within a new object is not
        incorrectly marked as recursive
        """
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        data = {"Test": ["a", "b", "c"]}
        encoder.encode(data)
        data = {"Previous": data, "Other": 400}
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Other": 400,
                          "Previous": {"Test": ["a", "b", "c"]}})

    def test_encoding_oversized_recursive(self):
        """
        Test that encoding an object which requires trimming clips recursion
        correctly
        """
        data = {"Test": ["a" * 128 * 1024, "b", "c"], "Other": {"a": 300}}
        data["Self"] = data
        encoder = SanitizingJSONEncoder(keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a" * 1024, "b", "c"],
                          "Self": "[RECURSIVE]",
                          "Other": {"a": 300}})

    def test_encoding_time(self):
        """
        Test that encoding a large object is sufficiently speedy
        """
        setup = """\
import json
from tests.large_object import large_object_file_path
from bugsnag.utils import SanitizingJSONEncoder
encoder = SanitizingJSONEncoder(keyword_filters=[])
with open(large_object_file_path()) as json_data:
    data = json.load(json_data)
        """
        stmt = """\
encoder.encode(data)
        """
        time = timeit.timeit(stmt=stmt, setup=setup, number=1000)
        maximum_time = 6
        if sys.version_info[0:2] <= (2, 6):
            # json encoding is very slow on python 2.6 so we need to increase
            # the allowable time when running on it
            maximum_time = 18
        self.assertTrue(time < maximum_time,
                        "Encoding required {0}s (expected {1}s)".format(
                            time, maximum_time
                        ))

    def test_filter_string_values_list_handling(self):
        """
        Test that filter_string_values can accept a list for the ignored
        parameter for backwards compatibility
        """
        data = {}
        encoder = SanitizingJSONEncoder()
        # no assert as we are just expecting this not to throw
        encoder.filter_string_values(data, ['password'])

    def test_sanitize_list_handling(self):
        """
        Test that _sanitize can accept a list for the ignored parameter for
        backwards compatibility
        """
        data = {}
        encoder = SanitizingJSONEncoder()
        # no assert as we are just expecting this not to throw
        encoder._sanitize(data, ['password'], ['password'])
