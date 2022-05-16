from functools import wraps, partial
import inspect
from json import JSONEncoder
from threading import local as threadlocal
from typing import AnyStr, Tuple, Optional
import warnings
import copy
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunsplit, parse_qs

MAX_PAYLOAD_LENGTH = 128 * 1024
MAX_STRING_LENGTH = 1024


__all__ = []  # type: ignore


class SanitizingJSONEncoder(JSONEncoder):
    """
    A JSON encoder which handles filtering and conversion from JSON-
    incompatible types to strings.

    >>> import logging
    >>> from json import loads
    >>> logger = logging.getLogger(__name__)
    >>> encoder = SanitizingJSONEncoder(logger, keyword_filters=['bananas'])
    >>> items = loads(encoder.encode(FilterDict({'carrots': 4, 'bananas': 5})))
    >>> items['bananas']
    '[FILTERED]'
    >>> items['carrots']
    4
    """

    filtered_value = '[FILTERED]'
    recursive_value = '[RECURSIVE]'
    unencodeable_value = '[BADENCODING]'

    def __init__(self, logger: logging.Logger, keyword_filters=None, **kwargs):
        self.logger = logger
        self.filters = list(map(str.lower, keyword_filters or []))
        self.bytes_filters = [x.encode('utf-8') for x in self.filters]
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
                if self._should_filter(key):
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
            self.logger.exception('Could not add object to payload')
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
                self.logger.exception(
                    'Could not add sanitize key for dictionary, '
                    'dropping value.')
        if isinstance(key, str):
            clean_dict[key] = clean_value
        else:
            try:
                clean_dict[str(key)] = clean_value
            except Exception:
                self.logger.exception(
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

    def _should_filter(self, key):
        if isinstance(key, str):
            key_lower = key.lower()
            return any(f in key_lower for f in self.filters)

        if isinstance(key, bytes):
            key_lower = key.lower()
            return any(f in key_lower for f in self.bytes_filters)

        return False


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
validate_int_setter = partial(_validate_setter, (int,))


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
        local = ThreadContextVar.local_context()
        if hasattr(local, self.name):
            return getattr(local, self.name)

        if hasattr(self, 'default'):
            # Make a deep copy so that each thread starts with a fresh default
            result = copy.deepcopy(self.default)
            self.set(result)
            return result

        raise LookupError("No value for '{}'".format(self.name))

    def set(self, new_value):
        setattr(ThreadContextVar.local_context(), self.name, new_value)


def sanitize_url(url: AnyStr, config) -> Optional[str]:
    try:
        if isinstance(url, str):
            url_str = url
        else:
            url_str = str(url, encoding='utf-8', errors='replace')

        parsed = urlparse(url_str)

        # if there's no query string there's nothing to redact
        if not parsed.query:
            return url_str

        url_without_query = urlunsplit(
            # urlunsplit always requires 5 elements in this tuple
            (parsed.scheme, parsed.netloc, parsed.path, None, None)
        ).strip()

        query_parameters = parse_qs(parsed.query)
    except Exception:
        # if we can't parse the url or query string then we can't know if
        # there's anything to redact, so have to omit the URL entirely
        return None

    encoder = SanitizingJSONEncoder(config.logger, config.params_filters)
    redacted_parameter_dict = encoder.filter_string_values(query_parameters)

    filtered_value = SanitizingJSONEncoder.filtered_value
    redacted_parameters = []

    for key, values in redacted_parameter_dict.items():
        # if "values" has been redacted it's a string, otherwise it's a list
        if values == filtered_value:
            redacted_parameters.append(key + "=" + values)
        else:
            for value in values:
                redacted_parameters.append(key + "=" + value)

    return url_without_query + "?" + "&".join(redacted_parameters)


def remove_query_from_url(url: AnyStr) -> Optional[AnyStr]:
    try:
        parsed = urlparse(url)

        url_without_query = urlunsplit(
            # urlunsplit always requires 5 elements in this tuple
            (parsed.scheme, parsed.netloc, parsed.path, None, None)
        ).strip()
    except Exception:
        return None

    # If the returned url is empty then it did not have any of the components
    # we are interested in, so return None to indicate failure
    if not url_without_query:
        return None

    return url_without_query


# to_rfc3339: format a datetime instance to match to_rfc3339/iso8601 with
# milliseconds precision
# Python can do this natively from version 3.6, but we need to include a
# fallback implementation for Python 3.5
try:
    # this will raise if 'timespec' isn't supported
    datetime.utcnow().isoformat(timespec='milliseconds')  # type: ignore

    def to_rfc3339(dt: datetime) -> str:
        return dt.isoformat(timespec='milliseconds')  # type: ignore

except Exception:
    def _get_timezone_offset(dt: datetime) -> str:
        if dt.tzinfo is None:
            return ''

        utc_offset = dt.tzinfo.utcoffset(dt)

        if utc_offset is None:
            return ''

        sign = '+'

        if utc_offset.days < 0:
            sign = '-'
            utc_offset = -utc_offset

        hours_offset, minutes = divmod(utc_offset, timedelta(hours=1))
        minutes_offset, seconds = divmod(minutes, timedelta(minutes=1))

        return '{:s}{:02d}:{:02d}'.format(sign, hours_offset, minutes_offset)

    def to_rfc3339(dt: datetime) -> str:
        return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:03d}{:s}'.format(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            int(dt.microsecond / 1000),
            _get_timezone_offset(dt)
        )
