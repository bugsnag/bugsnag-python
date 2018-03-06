from __future__ import division, print_function, absolute_import

import inspect
import six
from json import JSONEncoder
from threading import local as threadlocal

import bugsnag

MAX_PAYLOAD_LENGTH = 128 * 1024
MAX_STRING_LENGTH = 1024


class SanitizingJSONEncoder(JSONEncoder):
    """
    A JSON encoder which handles filtering and conversion from JSON-
    incompatible types to strings.

    >>> encoder = SanitizingJSONEncoder(filters=['bananas'])
    >>> encoder.encode({'carrots': 4, 'bananas': 5})
    "{'carrots': 4, 'bananas': '[FILTERED]'}"
    """

    filtered_value = '[FILTERED]'
    recursive_value = '[RECURSIVE]'
    unencodeable_value = '[BADENCODING]'

    def __init__(self, keyword_filters=None, **kwargs):
        self.filters = list(map(str.lower, keyword_filters or []))
        super(SanitizingJSONEncoder, self).__init__(**kwargs)

    def encode(self, obj):
        safe_obj = self._sanitize(obj, False)
        payload = super(SanitizingJSONEncoder, self).encode(safe_obj)
        if len(payload) > MAX_PAYLOAD_LENGTH:
            safe_obj = self._sanitize(safe_obj, True)
            return super(SanitizingJSONEncoder, self).encode(safe_obj)
        else:
            return payload

    def filter_string_values(self, obj, ignored=None):
        """
        Remove any value from the dictionary which match the key filters
        """
        if not ignored:
            ignored = []

        if id(obj) in ignored:
            return self.recursive_value

        if isinstance(obj, dict):
            ignored.append(id(obj))

            clean_dict = {}
            for key, value in six.iteritems(obj):
                is_string = isinstance(key, six.string_types)
                if is_string and any(f in key.lower() for f in self.filters):
                    clean_dict[key] = self.filtered_value
                else:
                    clean_dict[key] = self.filter_string_values(value, ignored)

            return clean_dict

        return obj

    def default(self, obj):
        """
        Coerce values to strings if possible, otherwise replace with
        '[BADENCODING]'
        """
        try:
            if six.PY3 and isinstance(obj, bytes):
                return six.text_type(obj, encoding='utf-8', errors='replace')
            else:
                return six.text_type(obj)

        except Exception:
            bugsnag.logger.exception('Could not add object to payload')
            return self.unencodeable_value

    def _sanitize(self, obj, trim_strings, ignored=None):
        """
        Replace recursive values and trim strings longer than
        MAX_STRING_LENGTH
        """
        if not ignored:
            ignored = []

        if id(obj) in ignored:
            return self.recursive_value
        elif isinstance(obj, dict):
            ignored.append(id(obj))
            return self._sanitize_dict(obj, trim_strings, ignored)
        elif isinstance(obj, (set, tuple, list)):
            ignored.append(id(obj))
            items = []
            for value in obj:
                items.append(self._sanitize(value, trim_strings, ignored))
            return items
        elif trim_strings and isinstance(obj, six.string_types):
            return obj[:MAX_STRING_LENGTH]
        else:
            return obj

    def _sanitize_dict(self, obj, trim_strings, ignored):
        """
        Trim individual values in an object, applying filtering if the object
        is a FilterDict
        """
        if isinstance(obj, FilterDict):
            obj = self.filter_string_values(obj)

        clean_dict = {}
        for key, value in six.iteritems(obj):
            clean_dict[key] = self._sanitize(value, trim_strings, ignored)

        return clean_dict


class FilterDict(dict):
    """
    Object which will be filtered when encoded
    """
    pass


def fully_qualified_class_name(obj):
    module = inspect.getmodule(obj)
    if module is not None and module.__name__ != "__main__":
        return module.__name__ + "." + obj.__class__.__name__
    else:
        return obj.__class__.__name__


def package_version(package_name):
    try:
        import pkg_resources
    except ImportError:
        return None
    else:
        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            return None


def merge_dicts(lhs, rhs):
    for key, value in rhs.items():
        if isinstance(value, dict):
            node = lhs.setdefault(key, {})
            merge_dicts(node, value)
        elif isinstance(value, list):
            array = lhs.setdefault(key, [])
            array += value
        else:
            lhs[key] = value


class ThreadLocals(object):
    LOCALS = None

    @staticmethod
    def get_instance():
        if not ThreadLocals.LOCALS:
            ThreadLocals.LOCALS = threadlocal()
        return ThreadLocals()

    def get_item(self, key, default=None):
        return getattr(ThreadLocals.LOCALS, key, default)

    def set_item(self, key, value):
        return setattr(ThreadLocals.LOCALS, key, value)

    def has_item(self, key):
        return hasattr(ThreadLocals.LOCALS, key)

    def del_item(self, key):
        return delattr(ThreadLocals.LOCALS, key)
