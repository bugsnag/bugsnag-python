import sys
import unittest
from bugsnag.utils import json_encode, sanitize_object
from nose.tools import eq_

@unittest.skipIf((3,0) <= sys.version_info < (3,3), "unicode string helper only support python3 >= 3.3")
class UtilTestCase(unittest.TestCase):
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
          "unicode": u"string",
          "obj": Exception(),
          "valid_unicode": u"\u2603",
      }

      # Sanitize our object
      sane_dict = sanitize_object(crazy_dict, filters=filters)

      # Check the values have been sanitized
      assert(sane_dict["password"] == "[FILTERED]")
      assert(sane_dict["metadata"]["another_password"] == "[FILTERED]")
      assert(sane_dict["metadata"]["regular"] == "text")
      assert("things" in sane_dict["list"])

  def test_json_encode(self):

      payload = {"a": u"a" * 512 * 1024}
      eq_(json_encode(payload), ('{"a": "' + 'a' * 1024 + '"}').encode('utf-8', 'replace'))
