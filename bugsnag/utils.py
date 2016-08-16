from __future__ import division, print_function, absolute_import

import inspect
import traceback
import six
from json import JSONEncoder

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
        print(self.filters)
        self.ignored = []
        super(SanitizingJSONEncoder, self).__init__(**kwargs)

    def encode(self, obj):
        safe_obj = self._sanitize(obj, False)
        payload = super(SanitizingJSONEncoder, self).encode(safe_obj)
        if len(payload) > MAX_PAYLOAD_LENGTH:
            safe_obj = self._sanitize(safe_obj, True)
            return super(SanitizingJSONEncoder, self).encode(safe_obj)
        else:
            return payload

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
            exc = traceback.format_exc()
            bugsnag.warn("Could not add object to payload: %s" % exc)
            return self.unencodeable_value

    def _sanitize(self, obj, trim_strings):
        """
        Replace recursive values and trim strings longer than
        MAX_STRING_LENGTH
        """
        if id(obj) in self.ignored:
            return self.recursive_value
        elif isinstance(obj, dict):
            self.ignored.append(id(obj))
            return self._sanitize_dict(obj, trim_strings)
        elif isinstance(obj, (set, tuple, list)):
            self.ignored.append(id(obj))
            return list(self._sanitize(value, trim_strings) for value in obj)
        elif trim_strings and isinstance(obj, six.string_types):
            return obj[:MAX_STRING_LENGTH]
        else:
            return obj

    def _sanitize_dict(self, obj, trim_strings):
        """
        Remove any value from the dictionary which match the key filters
        """
        clean_dict = {}
        for key, value in six.iteritems(obj):
            is_string = isinstance(key, six.string_types)
            if is_string and any(f in key.lower() for f in self.filters):
                clean_dict[key] = self.filtered_value
            else:
                clean_dict[key] = self._sanitize(value, trim_strings)

        return clean_dict


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
