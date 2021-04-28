from __future__ import division, print_function, absolute_import

from functools import wraps, partial
import inspect
import six
from json import JSONEncoder
from threading import local as threadlocal
import warnings
import copy

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

    def filter_string_values(self, obj, ignored=None, seen=None):
        """
        Remove any value from the dictionary which match the key filters
        """
        if not ignored:
            ignored = set()

        # Keep track of nested objects to avoid having references garbage
        # collected (which would cause id reuse and false positive recursion
        if seen is None:
            seen = []

        if type(ignored) is list:
            ignored = set(ignored)

        if id(obj) in ignored:
            return self.recursive_value

        if isinstance(obj, dict):
            ignored.add(id(obj))
            seen.append(obj)

            clean_dict = {}
            for key, value in six.iteritems(obj):
                is_string = isinstance(key, six.string_types)
                if is_string and any(f in key.lower() for f in self.filters):
                    clean_dict[key] = self.filtered_value
                else:
                    clean_dict[key] = self.filter_string_values(
                        value, ignored, seen)

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

    def _sanitize(self, obj, trim_strings, ignored=None, seen=None):
        """
        Replace recursive values and trim strings longer than
        MAX_STRING_LENGTH
        """
        if not ignored:
            ignored = set()

        # Keep track of nested objects to avoid having references garbage
        # collected (which would cause id reuse and false positive recursion)
        if seen is None:
            seen = []

        if type(ignored) is list:
            ignored = set(ignored)

        if id(obj) in ignored:
            return self.recursive_value
        elif isinstance(obj, dict):
            ignored.add(id(obj))
            seen.append(obj)
            return self._sanitize_dict(obj, trim_strings, ignored, seen)
        elif isinstance(obj, (set, tuple, list)):
            ignored.add(id(obj))
            seen.append(obj)
            items = []
            for value in obj:
                items.append(
                        self._sanitize(value, trim_strings, ignored, seen))
            return items
        elif trim_strings and isinstance(obj, six.string_types):
            return obj[:MAX_STRING_LENGTH]
        else:
            return obj

    def _sanitize_dict_key_value(self, clean_dict, key, clean_value):
        """
        Safely sets the provided key on the dictionary by coercing the key
        to a string
        """
        if six.PY3 and isinstance(key, bytes):
            try:
                key = six.text_type(key, encoding='utf-8', errors='replace')
                clean_dict[key] = clean_value
            except Exception:
                bugsnag.logger.exception(
                    'Could not add sanitize key for dictionary, '
                    'dropping value.')
        if isinstance(key, six.string_types):
            clean_dict[key] = clean_value
        else:
            try:
                clean_dict[str(key)] = clean_value
            except Exception:
                bugsnag.logger.exception(
                    'Could not add sanitize key for dictionary, '
                    'dropping value.')

    def _sanitize_dict(self, obj, trim_strings, ignored, seen):
        """
        Trim individual values in an object, applying filtering if the object
        is a FilterDict
        """
        if isinstance(obj, FilterDict):
            obj = self.filter_string_values(obj)

        clean_dict = {}
        for key, value in six.iteritems(obj):

            clean_value = self._sanitize(value, trim_strings, ignored, seen)

            self._sanitize_dict_key_value(clean_dict, key, clean_value)

        return clean_dict


class FilterDict(dict):
    """
    Object which will be filtered when encoded
    """
    pass


def parse_content_type(value):
    """
    Generate a tuple of (type, subtype, suffix, parameters) from a type based
    on RFC 6838

    >>> parse_content_type("text/plain")
    >>> ("text", "plain", None, None)
    >>> parse_content_type("application/hal+json")
    >>> ("application", "hal", "json", None)
    >>> parse_content_type("application/json;schema=\"https://example.com/a\"")
    >>> ("application", "json", None, "schema=https://example.com/a")
    """
    if ';' in value:
        types, parameters = value.split(';', 1)
    else:
        types, parameters = value, None
    if '/' in types:
        maintype, subtype = types.split('/', 1)
        if '+' in subtype:
            subtype, suffix = subtype.split('+', 1)
            return (maintype, subtype, suffix, parameters)
        else:
            return (maintype, subtype, None, parameters)
    else:
        return (types, None, None, parameters)


def is_json_content_type(value):  # type: (str) -> bool
    """
    Check if a content type is JSON-parseable

    >>> is_json_content_type('text/plain')
    >>> False
    >>> is_json_content_type('application/schema+json')
    >>> True
    >>> is_json_content_type('application/json')
    >>> True
    """
    type, subtype, suffix, _ = parse_content_type(value.lower())
    return type == 'application' and (subtype == 'json' or suffix == 'json')


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


def _validate_setter(types, func, future_error=False):
    """
    Check that the first argument of a function is of a provided set of types
    before calling the body of the wrapped function, printing a runtime warning
    if the validation fails.
    """
    @wraps(func)
    def wrapper(obj, value):
        option_name = func.__name__
        if value is None or isinstance(value, types):
            func(obj, value)
        else:
            error_format = '{0} should be {1}, got {2}'
            if future_error:
                error_format += '. This will be an error in a future release.'
            actual = type(value).__name__
            if types == six.string_types:
                requirement = 'str'
            else:
                requirement = ' or '.join([t.__name__ for t in types])
            message = error_format.format(option_name, requirement, actual)
            warnings.warn(message, RuntimeWarning)
    return wrapper


validate_str_setter = partial(_validate_setter, six.string_types)
validate_required_str_setter = partial(_validate_setter, six.string_types,
                                       future_error=True)
validate_bool_setter = partial(_validate_setter, (bool,))
validate_iterable_setter = partial(_validate_setter, (list, tuple))


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


class ThreadContextVar(object):
    """
    A wrapper around ThreadLocals to mimic the API of contextvars
    """
    def __init__(self, name, **kwargs):
        self.name = name

        # Mimic the behaviour of ContextVar - if a default has been explicitly
        # passed then we will use it, otherwise don't set an initial value
        # This allows 'get' to know when to raise a LookupError
        if 'default' in kwargs:
            self.default = kwargs['default']
            # Make a deep copy so this thread starts with a fresh default
            self.set(copy.deepcopy(self.default))

    def get(self):
        local = ThreadLocals.get_instance()

        if local.has_item(self.name):
            return local.get_item(self.name)

        if hasattr(self, 'default'):
            # Make a deep copy so that each thread starts with a fresh default
            result = copy.deepcopy(self.default)
            self.set(result)
            return result

        raise LookupError("No value for '{}'".format(self.name))

    def set(self, new_value):
        ThreadLocals.get_instance().set_item(self.name, new_value)
