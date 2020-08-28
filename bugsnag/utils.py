from functools import wraps, partial
import inspect
from json import JSONEncoder
from threading import local as threadlocal
from typing import Tuple, Optional
import warnings

import bugsnag

MAX_PAYLOAD_LENGTH = 128 * 1024
MAX_STRING_LENGTH = 1024


__all__ = []  # type: ignore


class SanitizingJSONEncoder(JSONEncoder):
    """
    A JSON encoder which handles filtering and conversion from JSON-
    incompatible types to strings.

    >>> from json import loads
    >>> encoder = SanitizingJSONEncoder(keyword_filters=['bananas'])
    >>> items = loads(encoder.encode(FilterDict({'carrots': 4, 'bananas': 5})))
    >>> items['bananas']
    '[FILTERED]'
    >>> items['carrots']
    4
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
            for key, value in obj.items():
                is_string = isinstance(key, str)
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
            if isinstance(obj, bytes):
                return str(obj, encoding='utf-8', errors='replace')
            else:
                return str(obj)

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
        elif trim_strings and isinstance(obj, str):
            return obj[:MAX_STRING_LENGTH]
        else:
            return obj

    def _sanitize_dict_key_value(self, clean_dict, key, clean_value):
        """
        Safely sets the provided key on the dictionary by coercing the key
        to a string
        """
        if isinstance(key, bytes):
            try:
                key = str(key, encoding='utf-8', errors='replace')
                clean_dict[key] = clean_value
            except Exception:
                bugsnag.logger.exception(
                    'Could not add sanitize key for dictionary, '
                    'dropping value.')
        if isinstance(key, str):
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
        for key, value in obj.items():

            clean_value = self._sanitize(value, trim_strings, ignored, seen)

            self._sanitize_dict_key_value(clean_dict, key, clean_value)

        return clean_dict


class FilterDict(dict):
    """
    Object which will be filtered when encoded
    """
    pass


ContentType = Tuple[str, Optional[str], Optional[str], Optional[str]]


def parse_content_type(value: str) -> ContentType:
    """
    Generate a tuple of (type, subtype, suffix, parameters) from a type based
    on RFC 6838

    >>> parse_content_type("text/plain")
    ('text', 'plain', None, None)
    >>> parse_content_type("application/hal+json")
    ('application', 'hal', 'json', None)
    >>> parse_content_type("application/json;schema=\\"ftp://example.com/a\\"")
    ('application', 'json', None, 'schema="ftp://example.com/a"')
    """
    parameters = None  # type: Optional[str]
    if ';' in value:
        types, parameters = value.split(';', 1)
    else:
        types = value
    if '/' in types:
        maintype, subtype = types.split('/', 1)
        if '+' in subtype:
            subtype, suffix = subtype.split('+', 1)
            return (maintype, subtype, suffix, parameters)
        else:
            return (maintype, subtype, None, parameters)
    else:
        return (types, None, None, parameters)


def is_json_content_type(value: str) -> bool:
    """
    Check if a content type is JSON-parseable

    >>> is_json_content_type('text/plain')
    False
    >>> is_json_content_type('application/schema+json')
    True
    >>> is_json_content_type('application/json')
    True
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


def _validate_setter(types, func, should_error=False):
    """
    Check that the first argument of a function is of a provided set of types
    before calling the body of the wrapped function, printing a runtime warning
    (or raising a TypeError) if the validation fails.
    """
    @wraps(func)
    def wrapper(obj, value):
        option_name = func.__name__
        if value is None or isinstance(value, types):
            func(obj, value)
        else:
            error_format = '{0} should be {1}, got {2}'
            actual = type(value).__name__
            requirement = ' or '.join([t.__name__ for t in types])
            message = error_format.format(option_name, requirement, actual)
            if should_error:
                raise TypeError(message)
            else:
                warnings.warn(message, RuntimeWarning)
    return wrapper


validate_str_setter = partial(_validate_setter, (str,))
validate_required_str_setter = partial(_validate_setter, (str,),
                                       should_error=True)
validate_bool_setter = partial(_validate_setter, (bool,))
validate_iterable_setter = partial(_validate_setter, (list, tuple))


class ThreadContextVar:
    """
    A wrapper around thread-local variables to mimic the API of contextvars
    """
    LOCALS = None

    @classmethod
    def local_context(cls):
        if not ThreadContextVar.LOCALS:
            ThreadContextVar.LOCALS = threadlocal()
        return ThreadContextVar.LOCALS

    def __init__(self, name, default=None):
        self.name = name
        setattr(ThreadContextVar.local_context(), name, default)

    def get(self):
        local = ThreadContextVar.local_context()
        if hasattr(local, self.name):
            return getattr(local, self.name)
        raise LookupError("No value for '{}'".format(self.name))

    def set(self, new_value):
        setattr(ThreadContextVar.local_context(), self.name, new_value)
