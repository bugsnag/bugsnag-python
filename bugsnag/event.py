from typing import Any, Dict, Optional, List, Union  # noqa
import linecache
import logging
import os
import sys
import traceback
import inspect
import warnings
from copy import deepcopy

import bugsnag

from bugsnag.breadcrumbs import Breadcrumb
from bugsnag.notifier import _NOTIFIER_INFORMATION
from bugsnag.utils import (
    fully_qualified_class_name as class_name,
    FilterDict,
    SanitizingJSONEncoder
)
from bugsnag.error import Error
from bugsnag.feature_flags import FeatureFlag, FeatureFlagDelegate

__all__ = ('Event',)

if sys.version_info < (3, 11):
    try:
        from exceptiongroup import BaseExceptionGroup
    except ImportError:
        # we're on Python < 3.11 and exceptiongroup isn't installed
        # an empty tuple can be passed to 'isinstance' safely and will
        # always return false, so we default to that
        BaseExceptionGroup = ()


class Event:
    """
    An occurrence of an exception for delivery to Bugsnag
    """
    NOTIFIER_NAME = _NOTIFIER_INFORMATION['name']
    NOTIFIER_URL = _NOTIFIER_INFORMATION['url']
    PAYLOAD_VERSION = "4.0"
    SUPPORTED_SEVERITIES = ["info", "warning", "error"]

    def __init__(self, exception: BaseException, config, request_config,
                 **options):
        """
        Create a new event

        exception is the exception being reported.
        config is the global instance of bugsnag.Configuration
        request_config is the thread-local instance of bugsnag.Configuration
        (used by middleware)

        options can be used to override any of the configuration parameters:
            "api_key", "release_stage", "app_version", "hostname"
        and to provide the following top-level event payload keys:
            "user", "context", "severity", "grouping_hash", "metadata",
            ("user_id")
        or to provide the exception parameter:
            "traceback"
        All other keys will be sent as metadata to Bugsnag.
        """
        self._exception = exception
        self._original_error = exception

        self.options = options
        self.config = config
        self.request_config = request_config
        self.request = None  # type: Any
        self._breadcrumbs = [
            deepcopy(breadcrumb) for breadcrumb in config.breadcrumbs
        ]
        self._feature_flag_delegate = options.pop(
            'feature_flag_delegate',
            FeatureFlagDelegate()
        ).copy()

        def get_config(key):
            return options.pop(key, getattr(self.config, key))

        self.release_stage = get_config("release_stage")
        self.app_version = get_config("app_version")
        self.app_type = get_config("app_type")
        self.hostname = get_config("hostname")
        self.runtime_versions = get_config("runtime_versions")
        self.send_code = get_config("send_code")

        self.context = options.pop("context", None)
        self.severity = options.pop("severity", "warning")
        if self.severity not in self.SUPPORTED_SEVERITIES:
            self.severity = "warning"

        self.unhandled = options.pop("unhandled", False)
        self.severity_reason = options.pop(
            "severity_reason",
            {'type': 'handledException'}
        )

        self.user = options.pop("user", {})
        if "user_id" in options:
            self.user["id"] = options.pop("user_id")

        # for backwards compatibility we generate the first error's stacktrace
        # here and use it as 'self.stacktrace' and 'self.errors[0].stacktrace'
        # this allows mutations 'self.stacktrace' to be reflected in the errors
        # list, which is used to generate the JSON payload
        stacktrace = self._generate_stacktrace(
            self.options.pop(
                "traceback",
                getattr(exception, '__traceback__', sys.exc_info()[2])
            ),
            self.options.pop("source_func", None)
        )

        self._stacktrace = stacktrace
        self._errors = self._generate_error_list(exception, stacktrace)

        self.grouping_hash = options.pop("grouping_hash", None)
        self.api_key = options.pop("api_key", get_config("api_key"))

        self.session = None  # type: Optional[Dict]

        self.metadata = {}  # type: Dict[str, Dict[str, Any]]
        if 'meta_data' in options:
            warnings.warn('The Event "meta_data" argument has been replaced ' +
                          'with "metadata"', DeprecationWarning)
            for name, tab in options.pop("meta_data").items():
                self.add_tab(name, tab)

        for name, tab in options.pop('metadata', {}).items():
            self.add_tab(name, tab)

        for name, tab in options.items():
            self.add_tab(name, tab)

        if hasattr(exception, "__notes__"):
            self.add_tab(
                "exception notes",
                dict(enumerate(exception.__notes__)) # type: ignore # noqa
            )

    @property
    def meta_data(self) -> Dict[str, Dict[str, Any]]:
        warnings.warn('The Event "meta_data" property has been replaced ' +
                      'with "metadata".', DeprecationWarning)
        return self.metadata

    @property
    def breadcrumbs(self) -> List[Breadcrumb]:
        return self._breadcrumbs.copy()

    @property
    def errors(self) -> List[Error]:
        return self._errors.copy()

    @property
    def original_error(self) -> BaseException:
        return self._original_error

    @property
    def stacktrace(self) -> List[Dict[str, Any]]:
        warnings.warn(
            (
                'The Event "stacktrace" property has been deprecated in favour'
                ' of accessing the stacktrace of an error, for example '
                '"errors[0].stacktrace"'
            ),
            DeprecationWarning
        )

        return self._stacktrace

    @stacktrace.setter
    def stacktrace(self, value: List[Dict[str, Any]]) -> None:
        warnings.warn(
            (
                'The Event "stacktrace" property has been deprecated in favour'
                ' of accessing the stacktrace of an error, for example '
                '"errors[0].stacktrace"'
            ),
            DeprecationWarning
        )

        self._stacktrace = value
        self._errors[0].stacktrace = value

    @property
    def exception(self) -> BaseException:
        warnings.warn(
            (
                'The Event "exception" property has been replaced with '
                '"original_error"'
            ),
            DeprecationWarning
        )

        return self._exception

    @exception.setter
    def exception(self, value: BaseException) -> None:
        warnings.warn(
            (
                'Setting the Event "exception" property has been deprecated, '
                'update the "errors" list instead'
            ),
            DeprecationWarning
        )

        self._exception = value
        self._errors[0] = Error(
            class_name(value),
            str(value),
            self._stacktrace
        )

    def set_user(self, id=None, name=None, email=None):
        """
        Set user parameters on event.
        """
        if id:
            self.user["id"] = id
        if name:
            self.user["name"] = name
        if email:
            self.user["email"] = email

    def add_custom_data(self, key, value):
        """
        Add data to the "custom" metadata tab
        """
        self.add_tab("custom", {key: value})

    def add_tab(self, name, dictionary):
        """
        Add a metadata tab to the event

        If the tab already exists, the new content will be merged into the
        existing content.
        """
        if not isinstance(dictionary, dict):
            self.add_tab("custom", {name: dictionary})
            return

        if name not in self.metadata:
            self.metadata[name] = {}

        self.metadata[name].update(dictionary)

    @property
    def feature_flags(self) -> List[FeatureFlag]:
        return self._feature_flag_delegate.to_list()

    def add_feature_flag(
        self,
        name: Union[str, bytes],
        variant: Union[None, str, bytes] = None
    ) -> None:
        self._feature_flag_delegate.add(name, variant)

    def add_feature_flags(self, feature_flags: List[FeatureFlag]) -> None:
        self._feature_flag_delegate.merge(feature_flags)

    def clear_feature_flag(self, name: Union[str, bytes]) -> None:
        self._feature_flag_delegate.remove(name)

    def clear_feature_flags(self) -> None:
        self._feature_flag_delegate.clear()

    def _generate_error_list(
        self,
        exception: BaseException,
        first_error_stacktrace: List[Dict[str, Any]]
    ) -> List[Error]:
        error_list = [
            Error(
                class_name(exception),
                str(exception),
                first_error_stacktrace
            )
        ]

        if not isinstance(exception, BaseException):
            return error_list

        while True:
            if exception.__cause__:
                exception = exception.__cause__
            elif exception.__context__ and not exception.__suppress_context__:
                exception = exception.__context__
            else:
                break

            error_list.append(
                Error(
                    class_name(exception),
                    str(exception),
                    self._generate_stacktrace(exception.__traceback__)
                )
            )

        # unwrap BaseExceptionGroups so that their contained exceptions are
        # also reported
        # we don't recurse into nested BaseExceptionGroups or cause/context
        # here because there's a big risk of that leading to a huge number of
        # exceptions, which is difficult to reason about
        if isinstance(self._original_error, BaseExceptionGroup):
            for sub_exception in self._original_error.exceptions: # type: ignore # noqa
                error_list.append(
                    Error(
                        class_name(sub_exception),
                        str(sub_exception),
                        self._generate_stacktrace(sub_exception.__traceback__)
                    )
                )

        return error_list

    def _generate_stacktrace(
        self,
        tb,
        source_func=None
    ) -> List[Dict[str, Any]]:
        """
        Build the stacktrace
        """
        if tb:
            trace = traceback.extract_tb(tb)
        else:
            trace = traceback.extract_stack()

        bugsnag_module_path = os.path.dirname(bugsnag.__file__)
        logging_module_path = os.path.dirname(logging.__file__)
        exclude_module_paths = [bugsnag_module_path, logging_module_path]
        user_exclude_modules = self.config.traceback_exclude_modules
        for exclude_module in user_exclude_modules:
            try:
                module_file = exclude_module.__file__
                if module_file[-4:] == '.pyc':
                    module_file = module_file[:-1]
                exclude_module_paths.append(module_file)
            except Exception:
                self.config.logger.exception(
                    'Could not exclude module: %s' % repr(exclude_module))

        lib_root = self.config.lib_root
        if lib_root and lib_root[-1] != os.sep:
            lib_root += os.sep

        project_root = self.config.project_root
        if project_root and project_root[-1] != os.sep:
            project_root += os.sep

        stacktrace = []
        if source_func is not None:
            try:
                source = inspect.getsourcefile(source_func)
                lines = inspect.getsourcelines(source_func)
                line = 0
                if lines is not None and len(lines) > 1:
                    line = lines[1]

                trace.insert(
                    0,
                    [source, line, source_func.__name__]  # type: ignore
                )
            except (IOError, TypeError):
                pass

        for frame in trace:
            file_name = os.path.abspath(str(frame[0]))
            in_project = False

            skip_module = False
            for module_path in exclude_module_paths:
                if file_name.startswith(module_path):
                    skip_module = True
                    break
            if skip_module:
                continue

            # Fetch the code before (potentially) removing the project root
            # from the file path
            code = self._code_for(file_name, int(str(frame[1])))

            if lib_root and file_name.startswith(lib_root):
                file_name = file_name[len(lib_root):]
            elif project_root and file_name.startswith(project_root):
                file_name = file_name[len(project_root):]
                in_project = True

            stacktrace.append({
                "file": file_name,
                "lineNumber": int(str(frame[1])),
                "method": str(frame[2]),
                "inProject": in_project,
                "code": code
            })

        stacktrace.reverse()

        return stacktrace

    def _code_for(self, file_name, line, window_size=7):
        """
        Find the code around this line in the file.
        """
        if not self.send_code:
            return None

        try:
            lines = linecache.getlines(file_name)

            start = max(line - int(window_size / 2), 1)
            end = start + window_size

            # The last line of the file is len(lines). End of an
            # exclusive range is one greater.
            if end > len(lines) + 1:
                end = len(lines) + 1
                start = max(end - window_size, 1)

            return dict((n, lines[n - 1].rstrip()) for n in range(start, end))

        except Exception:
            return None

    def _payload(self):
        # Fetch the notifier version from the package
        encoder = SanitizingJSONEncoder(
            self.config.logger,
            separators=(',', ':'),
            keyword_filters=self.config.params_filters
        )

        # Construct the payload dictionary
        return encoder.encode({
            "apiKey": self.api_key,
            "notifier": _NOTIFIER_INFORMATION,
            "events": [{
                "severity": self.severity,
                "severityReason": self.severity_reason,
                "unhandled": self.unhandled,
                "releaseStage": self.release_stage,
                "app": {
                    "version": self.app_version,
                    "type": self.app_type,
                },
                "context": self.context,
                "groupingHash": self.grouping_hash,
                "exceptions": [
                    error.to_dict() for error in self.errors
                ],
                "metaData": FilterDict(self.metadata),
                "user": FilterDict(self.user),
                "device": FilterDict({
                    "hostname": self.hostname,
                    "runtimeVersions": self.runtime_versions
                }),
                "projectRoot": self.config.project_root,
                "libRoot": self.config.lib_root,
                "session": self.session,
                "breadcrumbs": [
                    breadcrumb.to_dict() for breadcrumb in self._breadcrumbs
                ],
                "featureFlags": self._feature_flag_delegate.to_json()
            }]
        })
