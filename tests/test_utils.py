import unittest
import json
import timeit
import sys
import datetime
import re

from six import u
from bugsnag.utils import SanitizingJSONEncoder, FilterDict, ThreadLocals


class TestUtils(unittest.TestCase):

    def test_filter_dict_with_inner_dict(self):
        data = {
            "level1-key1": {
                "level2-key1": FilterDict({
                    "level3-key1": {
                        'level4-key1': 'level4-value1'}
                }),
                "level2-key2": FilterDict({
                    "level3-key2": "level3-value1",
                    "level3-key3": {
                        'level4-key2': 'level4-value2'}
                }),
            }
        }
        encoder = SanitizingJSONEncoder(keyword_filters=["password"])
        sane_data = json.loads(encoder.encode(data))
        self.assertEqual(sane_data,
                         {
                            "level1-key1": {
                                "level2-key1": {
                                    "level3-key1": {
                                        'level4-key1': 'level4-value1'}
                                },
                                "level2-key2": {
                                    "level3-key2": "level3-value1",
                                    "level3-key3": {
                                        'level4-key2': 'level4-value2'}
                                },
                            }
                         })
