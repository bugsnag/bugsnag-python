import unittest
import json
import timeit
import re
import threading
import uuid
import logging
import pytest
from datetime import datetime, timedelta, timezone

from bugsnag.utils import (SanitizingJSONEncoder, FilterDict,
                           is_json_content_type, parse_content_type,
                           ThreadContextVar, to_rfc3339, remove_query_from_url)

logger = logging.getLogger(__name__)


class TestUtils(unittest.TestCase):
    def tearDown(self):
        super(TestUtils, self).tearDown()

    def test_encode_filters(self):
        data = FilterDict({"credit_card": "123213213123", "password": "456",
                           "cake": True})
        encoder = SanitizingJSONEncoder(
            logger,
            keyword_filters=["credit_card", "password"]
        )

        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"credit_card": "[FILTERED]",
                                     "password": "[FILTERED]",
                                     "cake": True})

    def test_encode_filters_object_key(self):
        object_key = object()
        data = FilterDict({"password": "456", object_key: True})

        encoder = SanitizingJSONEncoder(
            logger,
            keyword_filters=["password"]
        )

        actual = json.loads(encoder.encode(data))
        expected = {"password": "[FILTERED]", str(object_key): True}

        self.assertEqual(actual, expected)

    def test_encode_filters_bytes(self):
        data = FilterDict({b"credit_card": "123213213123", b"password": "456",
                           "cake": True})
        encoder = SanitizingJSONEncoder(
            logger,
            keyword_filters=["credit_card", "password"]
        )

        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"credit_card": "[FILTERED]",
                                     "password": "[FILTERED]",
                                     "cake": True})

    def test_sanitize_list(self):
        data = FilterDict({"list": ["carrots", "apples", "peas"],
                           "passwords": ["abc", "def"]})

        encoder = SanitizingJSONEncoder(
            logger,
            keyword_filters=["credit_card", "passwords"]
        )

        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"list": ["carrots", "apples", "peas"],
                                     "passwords": "[FILTERED]"})

    def test_sanitize_valid_unicode_object(self):
        data = {"item": '\U0001f62c'}
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, data)

    def test_sanitize_nested_object_filters(self):
        data = FilterDict({"metadata": {"another_password": "My password"}})

        encoder = SanitizingJSONEncoder(
            logger,
            keyword_filters=["password"]
        )

        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"metadata": {"another_password": "[FILTERED]"}})

    def test_sanitize_bad_utf8_object(self):
        data = {"bad_utf8": "test \xe9"}
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, data)

    def test_sanitize_unencoded_object(self):
        data = {"exc": Exception()}
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"exc": ""})

    def test_json_encode(self):
        payload = {"a": "a" * 512 * 1024}
        expected = {"a": "a" * 1024}
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        self.assertEqual(json.loads(encoder.encode(payload)), expected)

    def test_filter_dict(self):
        data = FilterDict({"metadata": {"another_password": "My password"}})
        encoder = SanitizingJSONEncoder(logger, keyword_filters=["password"])
        sane_data = encoder.filter_string_values(data)
        self.assertEqual(sane_data,
                         {"metadata": {"another_password": "[FILTERED]"}})

    def test_decode_bytes(self):
        data = FilterDict({b"metadata": "value"})
        encoder = SanitizingJSONEncoder(logger, keyword_filters=["password"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {"metadata": "value"})

    def test_unfiltered_encode(self):
        data = {"metadata": {"another_password": "My password"}}
        encoder = SanitizingJSONEncoder(logger, keyword_filters=["password"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, data)

    def test_thread_context_vars_get_raises_if_no_default(self):
        token = ThreadContextVar(str(uuid.uuid4()))
        self.assertRaises(LookupError, token.get)

    def test_thread_context_vars_returns_default_value_from_get(self):
        token = ThreadContextVar(str(uuid.uuid4()), default={'pips': 3})
        self.assertEqual({'pips': 3}, token.get())

    def test_thread_context_vars_set_new_value_with_no_default(self):
        token = ThreadContextVar(str(uuid.uuid4()))
        token.set({'peas': 'maybe'})
        self.assertEqual({'peas': 'maybe'}, token.get())

    def test_thread_context_vars_set_new_value(self):
        token = ThreadContextVar(str(uuid.uuid4()), default={'pips': 3})
        token.set({'carrots': 'no'})
        self.assertEqual({'carrots': 'no'}, token.get())

    def test_thread_context_vars_in_thread(self):
        """
        Verify that ThreadContextVar backport has correct behavior
        inside a new thread.
        """
        token = ThreadContextVar(str(uuid.uuid4()), default={'pips': 3})
        token.set({'pips': 4})

        def thread_worker():
            try:
                thread.exc_info = None

                result = token.get()

                # Test that we got a new, unmodified copy of the default
                self.assertEqual({'pips': 3}, result)

                result['pips'] = 5

                # Test that local modifications are persistent
                self.assertEqual({'pips': 5}, token.get())
            except Exception:
                import sys
                thread.exc_info = sys.exc_info()

        thread = threading.Thread(target=thread_worker)
        thread.start()
        thread.join()

        # ensure exceptions in the thread_worker fail the test
        self.assertEqual(None, thread.exc_info, thread.exc_info)

        # Test that non-local changes don't leak through
        self.assertEqual({'pips': 4}, token.get())

    def test_encoding_recursive(self):
        """
        Test that recursive data structures are replaced with '[RECURSIVE]'
        """
        data = {"Test": ["a", "b", "c"]}
        data["Self"] = data
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a", "b", "c"], "Self": "[RECURSIVE]"})

    def test_encoding_recursive_repeated(self):
        """
        Test that encoding the same object twice produces the same result
        """
        data = {"Test": ["a", "b", "c"]}
        data["Self"] = data
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a", "b", "c"], "Self": "[RECURSIVE]"})
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"Test": ["a", "b", "c"], "Self": "[RECURSIVE]"})

    def test_encoding_identical_siblings(self):
        """
        Test encoding identical siblings
        """
        inner_list = [1, 2, 3]
        nested_list = [inner_list, inner_list]
        data = {"nested0": nested_list,
                "nested1": nested_list,
                "inner": inner_list}
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {"nested0": nested_list,
                          "nested1": nested_list,
                          "inner": inner_list})

    def test_encoding_nested_repeated(self):
        """
        Test that encoding the same object within a new object is not
        incorrectly marked as recursive
        """
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
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
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
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
import logging
from tests.large_object import large_object_file_path
from bugsnag.utils import SanitizingJSONEncoder

logger = logging.getLogger(__name__)
encoder = SanitizingJSONEncoder(logger, keyword_filters=[])
with open(large_object_file_path()) as json_data:
    data = json.load(json_data)
        """

        stmt = "encoder.encode(data)"

        time = timeit.timeit(stmt=stmt, setup=setup, number=1000)
        maximum_time = 6

        self.assertTrue(
            time < maximum_time,
            "Encoding required {0}s (expected {1}s)".format(time, maximum_time)
        )

    def test_filter_string_values_list_handling(self):
        """
        Test that filter_string_values can accept a list for the ignored
        parameter for backwards compatibility
        """
        data = {}
        encoder = SanitizingJSONEncoder(logger)
        # no assert as we are just expecting this not to throw
        encoder.filter_string_values(data, ['password'])

    def test_sanitize_list_handling(self):
        """
        Test that _sanitize can accept a list for the ignored parameter for
        backwards compatibility
        """
        data = {}
        encoder = SanitizingJSONEncoder(logger)
        # no assert as we are just expecting this not to throw
        encoder._sanitize(data, ['password'], ['password'])

    def test_json_encode_invalid_keys(self):
        """
        Test that _sanitize can accept some invalid json where a function
        name or some other bad data is passed as a key in the payload
        dictionary.
        """
        encoder = SanitizingJSONEncoder(logger, keyword_filters=[])

        def foo():
            return "123"

        result = json.loads(encoder.encode({foo: "a"}))
        self.assertTrue(re.match(r'<function.*foo.*',
                                 list(result.keys())[0]) is not None)
        self.assertEqual(list(result.values()), ["a"])

        now = datetime.now()
        result = json.loads(encoder.encode({now: "a"}))
        self.assertEqual(list(result.keys())[0], str(now))
        self.assertEqual(list(result.values()), ["a"])

        class Object(object):
            pass

        result = json.loads(encoder.encode({Object(): "a"}))
        self.assertTrue(re.match(r'<tests.test_utils.*Object.*',
                                 list(result.keys())[0]) is not None)
        self.assertEqual(list(result.values()), ["a"])

    def test_filter_dict_with_inner_dict(self):
        """
        Test that nested dict uniqueness checks work and are not recycled
        when a reference to a nested dict goes out of scope
        """
        data = {
            'level1-key1': {
                'level2-key1': FilterDict({
                    'level3-key1': {'level4-key1': 'level4-value1'},
                    'level3-key4': {'level4-key3': 'level4-value3'},
                }),
                'level2-key2': FilterDict({
                    'level3-key2': 'level3-value1',
                    'level3-key3': {'level4-key2': 'level4-value2'},
                    'level3-key5': {'level4-key4': 'level4-value4'},
                }),
            }
        }
        encoder = SanitizingJSONEncoder(logger, keyword_filters=['password'])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data, {
                            'level1-key1': {
                                'level2-key1': {
                                    'level3-key1': {
                                        'level4-key1': 'level4-value1'
                                    },
                                    'level3-key4': {
                                        'level4-key3': 'level4-value3'
                                    }
                                },
                                'level2-key2': {
                                    'level3-key2': 'level3-value1',
                                    'level3-key3': {
                                        'level4-key2': 'level4-value2'
                                    },
                                    'level3-key5': {
                                        'level4-key4': 'level4-value4'
                                    },
                                },
                            }
                        })

    def test_filter_strings_with_inner_dict(self):
        """
        Test that nested dict uniqueness checks work and are not recycled
        when a reference to a nested dict goes out of scope
        """
        data = FilterDict({
            'level1-key1': {
                'level2-key1': {
                    'level3-key1': {'level4-key1': 'level4-value1'},
                    'token': 'mypassword',
                },
                'level2-key2': {
                    'level3-key3': {'level4-key2': 'level4-value2'},
                    'level3-key4': {'level4-key3': 'level4-value3'},
                    'level3-key5': {'password': 'super-secret'},
                    'level3-key6': {'level4-key4': 'level4-value4'},
                    'level3-key7': {'level4-key4': 'level4-value4'},
                    'level3-key8': {'level4-key4': 'level4-value4'},
                    'level3-key9': {'level4-key4': 'level4-value4'},
                    'level3-key0': {'level4-key4': 'level4-value4'},
                },
            }
        })

        encoder = SanitizingJSONEncoder(
            logger,
            keyword_filters=['password', 'token']
        )

        filtered_data = encoder.filter_string_values(data)
        self.assertEqual(filtered_data, {
                            'level1-key1': {
                                'level2-key1': {
                                    'level3-key1': {
                                        'level4-key1': 'level4-value1'
                                    },
                                    'token': '[FILTERED]'
                                },
                                'level2-key2': {
                                    'level3-key3': {
                                        'level4-key2': 'level4-value2'
                                    },
                                    'level3-key4': {
                                        'level4-key3': 'level4-value3'
                                    },
                                    'level3-key5': {
                                        'password': '[FILTERED]'
                                    },
                                    'level3-key6': {
                                        'level4-key4': 'level4-value4'
                                    },
                                    'level3-key7': {
                                        'level4-key4': 'level4-value4'
                                    },
                                    'level3-key8': {
                                        'level4-key4': 'level4-value4'
                                    },
                                    'level3-key9': {
                                        'level4-key4': 'level4-value4'
                                    },
                                    'level3-key0': {
                                        'level4-key4': 'level4-value4'
                                    },
                                },
                            }
                        })

    def test_parse_invalid_content_type(self):
        info = parse_content_type('invalid-type')
        self.assertEqual(('invalid-type', None, None, None), info)

    def test_parse_invalid_content_type_params(self):
        info = parse_content_type('invalid-type;schema=http://example.com/b')
        self.assertEqual(('invalid-type', None, None,
                          'schema=http://example.com/b'), info)

    def test_parse_parameters(self):
        info = parse_content_type('text/plain;charset=utf-32')
        self.assertEqual(('text', 'plain', None, 'charset=utf-32'), info)

    def test_parse_suffix(self):
        info = parse_content_type('application/hal+json;charset=utf-8')
        self.assertEqual(('application', 'hal', 'json', 'charset=utf-8'), info)

    def test_json_content_type(self):
        self.assertTrue(is_json_content_type('application/json'))
        self.assertTrue(is_json_content_type('application/hal+json'))
        self.assertTrue(is_json_content_type('application/other+json'))
        self.assertTrue(is_json_content_type(
            'application/schema+json;schema=http://example.com/schema-2'))
        self.assertTrue(is_json_content_type('application/json;charset=utf-8'))
        self.assertFalse(is_json_content_type('text/json'))
        self.assertFalse(is_json_content_type('text/plain'))
        self.assertFalse(is_json_content_type('json'))
        self.assertFalse(is_json_content_type('application/jsonfoo'))


utc = timezone.utc
plus_1 = timezone(timedelta(hours=1))
plus_12 = timezone(timedelta(hours=12))
plus_0_15 = timezone(timedelta(hours=0, minutes=15))
plus_12_30 = timezone(timedelta(hours=12, minutes=30))
minus_1 = timezone(timedelta(hours=-1))
minus_12 = timezone(timedelta(hours=-12))
minus_0_15 = timezone(timedelta(hours=0, minutes=-15))
minus_12_30 = timezone(timedelta(hours=-12, minutes=-30))


@pytest.mark.parametrize("dt, expected", [
    (datetime(1, 1, 1, 1, 1, 1, 1), '0001-01-01T01:01:01.000'),  # noqa: E501
    (datetime(1900, 1, 2, 3, 4, 5, 678900), '1900-01-02T03:04:05.678'),  # noqa: E501
    (datetime(9999, 12, 31, 23, 59, 59, 999999), '9999-12-31T23:59:59.999'),  # noqa: E501
    (datetime(1950, 5, 14, 20, 34, 52, 61000), '1950-05-14T20:34:52.061'),  # noqa: E501
    (datetime(1999, 4, 3, 14, 7, 12), '1999-04-03T14:07:12.000'),  # noqa: E501
    (datetime(2021, 1, 1, tzinfo=timezone.utc), '2021-01-01T00:00:00.000+00:00'),  # noqa: E501
    (datetime(1, 1, 1, 1, 1, 1, 1, tzinfo=plus_1), '0001-01-01T01:01:01.000+01:00'),  # noqa: E501
    (datetime(1900, 1, 2, 3, 4, 5, 678900, tzinfo=plus_12), '1900-01-02T03:04:05.678+12:00'),  # noqa: E501
    (datetime(1999, 4, 3, 14, 7, 12, tzinfo=plus_0_15), '1999-04-03T14:07:12.000+00:15'),  # noqa: E501
    (datetime(1950, 5, 14, 20, 34, 52, 61000, tzinfo=plus_12_30), '1950-05-14T20:34:52.061+12:30'),  # noqa: E501
    (datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=minus_1), '9999-12-31T23:59:59.999-01:00'),  # noqa: E501
    (datetime(1950, 5, 14, 20, 34, 52, 61000, tzinfo=minus_12), '1950-05-14T20:34:52.061-12:00'),  # noqa: E501
    (datetime(1999, 4, 3, 14, 7, 12, tzinfo=minus_0_15), '1999-04-03T14:07:12.000-00:15'),  # noqa: E501
    (datetime(1950, 5, 14, 20, 34, 52, 61000, tzinfo=minus_12_30), '1950-05-14T20:34:52.061-12:30'),  # noqa: E501
])
def test_to_rfc3339(dt: datetime, expected: str):
    assert to_rfc3339(dt) == expected


@pytest.mark.parametrize("url, expected", [
    ('https://example.com', 'https://example.com'),
    ('https://example.com/', 'https://example.com/'),
    ('https://example.com/a/b/c', 'https://example.com/a/b/c'),
    ('https://example.com/abc?xyz=123', 'https://example.com/abc'),
    ('https://example.com/a/b/c', 'https://example.com/a/b/c'),
    ('https://example.com/abc?xyz=123', 'https://example.com/abc'),
    ('https://example.com/abc;x=1;y=2;z=3', 'https://example.com/abc'),
    ('https://example.com:8000/abc?xyz=123', 'https://example.com:8000/abc'),
    (b'https://example.com', b'https://example.com'),
    (b'https://example.com/', b'https://example.com/'),
    (b'https://example.com/a/b/c', b'https://example.com/a/b/c'),
    (b'https://example.com/abc?xyz=123', b'https://example.com/abc'),
    (b'https://example.com/a/b/c', b'https://example.com/a/b/c'),
    (b'https://example.com/abc?xyz=123', b'https://example.com/abc'),
    (b'https://example.com/abc;x=1;y=2;z=3', b'https://example.com/abc'),
    (b'https://example.com:8000/abc?xyz=123', b'https://example.com:8000/abc'),

    ('wss://example.com/abc?xyz=123', 'wss://example.com/abc'),
    ('ftp://example.com/abc?xyz=123', 'ftp://example.com/abc'),
    (b'wss://example.com/abc?xyz=123', b'wss://example.com/abc'),
    (b'ftp://example.com/abc?xyz=123', b'ftp://example.com/abc'),

    ('xyz', 'xyz'),
    ('///', '/'),
    ('/a/b/c', '/a/b/c'),
    ('example.com/<<<<', 'example.com/<<<<'),
    ('->example.com<-', '->example.com<-'),
    (b'xyz', b'xyz'),
    (b'///', b'/'),
    (b'/a/b/c', b'/a/b/c'),
    (b'example.com/<<<<', b'example.com/<<<<'),
    (b'->example.com<-', b'->example.com<-'),

    ('', None),
    (b'', None),
    ('  ', None),
    (b'  ', None),
    (None, None),
    (123, None),
    ([1, 2, 3], None),
    ({'a': 1, b'b': 2, 'c': 3}, None),
    (object(), None),
    (lambda: 'example.com', None),
])
def test_remove_query_from_url(url, expected):
    assert remove_query_from_url(url) == expected
