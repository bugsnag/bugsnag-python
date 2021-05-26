from typing import Any, Dict, Optional, List
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
from bugsnag.utils import fully_qualified_class_name as class_name
from bugsnag.utils import FilterDict, package_version, SanitizingJSONEncoder


__all__ = ('Event',)


class Event:
    """
    An occurrence of an exception for delivery to Bugsnag
    """
    NOTIFIER_NAME = "Python Bugsnag Notifier"
    NOTIFIER_URL = "https://github.com/bugsnag/bugsnag-python"
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
        self.exception = exception
        self.options = options
        self.config = config
        self.request_config = request_config
        self.request = None  # type: Any
        self._breadcrumbs = [
            deepcopy(breadcrumb) for breadcrumb in config.breadcrumbs
        ]

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

        self.stacktrace = self._generate_stacktrace(
            self.options.pop("traceback", sys.exc_info()[2]),
            self.options.pop("source_func", None))
        self.grouping_hash = options.pop("grouping_hash", None)
        self.api_key = options.pop("api_key", get_config("api_key"))

        self.session = None  # type: Optional[Dict]

        self.metadata = {}  # type: Dict[str, Dict[str, Any]]
        if 'meta_data' in options:
            warnings.warn('The Event "metadata" argument has been replaced ' +
                          'with "metadata"', DeprecationWarning)
            for name, tab in options.pop("meta_data").items():
                self.add_tab(name, tab)

        for name, tab in options.pop('metadata', {}).items():
            self.add_tab(name, tab)

        for name, tab in options.items():
            self.add_tab(name, tab)

    @property
    def meta_data(self) -> Dict[str, Dict[str, Any]]:
        warnings.warn('The Event "metadata" property has been replaced ' +
                      'with "meta_data".', DeprecationWarning)
        return self.metadata

    @property
    def breadcrumbs(self) -> List[Breadcrumb]:
        return self._breadcrumbs.copy()

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

    def _generate_stacktrace(self, tb, source_func=None):
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
                trace.insert(0, [source, line, source_func.__name__])
            except (IOError, TypeError):
                pass

        for line in trace:
            file_name = os.path.abspath(str(line[0]))
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
            code = self._code_for(file_name, int(str(line[1])))

            if lib_root and file_name.startswith(lib_root):
                file_name = file_name[len(lib_root):]
            elif project_root and file_name.startswith(project_root):
                file_name = file_name[len(project_root):]
                in_project = True

            stacktrace.append({
                "file": file_name,
                "lineNumber": int(str(line[1])),
                "method": str(line[2]),
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
        notifier_version = package_version("bugsnag") or "unknown"
        encoder = SanitizingJSONEncoder(
            self.config.logger,
            separators=(',', ':'),
            keyword_filters=self.config.params_filters
        )

        # Construct the payload dictionary
        return encoder.encode({
            "apiKey": self.api_key,
            "notifier": {
                "name": self.NOTIFIER_NAME,
                "url": self.NOTIFIER_URL,
                "version": notifier_version,
            },
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
                "exceptions": [{
                    "errorClass": class_name(self.exception),
                    "message": self.exception,
                    "stacktrace": self.stacktrace,
                }],
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
                ]
            }]
        })
