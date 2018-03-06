from __future__ import absolute_import, division, print_function

import linecache
import logging
import os
import sys
import traceback
import inspect

import bugsnag

from bugsnag.utils import fully_qualified_class_name as class_name
from bugsnag.utils import FilterDict, package_version, SanitizingJSONEncoder


class Notification(object):
    """
    A single exception notification to Bugsnag.
    """
    NOTIFIER_NAME = "Python Bugsnag Notifier"
    NOTIFIER_URL = "https://github.com/bugsnag/bugsnag-python"
    PAYLOAD_VERSION = "4.0"
    SUPPORTED_SEVERITIES = ["info", "warning", "error"]

    def __init__(self, exception, config, request_config, **options):
        """
        Create a new notification

        exception is the exception being reported.
        config is the global instance of bugsnag.Configuration
        request_config is the thread-local instance of bugsnag.Configuration
        (used by middleware)

        options can be used to override any of the configuration parameters:
            "api_key", "release_stage", "app_version", "hostname"
        and to provide the following top-level notification payload keys:
            "user", "context", "severity", "grouping_hash", "meta_data",
            ("user_id")
        or to provide the exception parameter:
            "traceback"
        All other keys will be sent as meta-data to Bugsnag.
        """
        self.exception = exception
        self.options = options
        self.config = config
        self.request_config = request_config

        def get_config(key):
            return options.pop(key, self.config.get(key))

        self.release_stage = get_config("release_stage")
        self.app_version = get_config("app_version")
        self.hostname = get_config("hostname")
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

        self.session = None

        self.meta_data = {}
        for name, tab in options.pop("meta_data", {}).items():
            self.add_tab(name, tab)

        for name, tab in options.items():
            self.add_tab(name, tab)

    def set_user(self, id=None, name=None, email=None):
        """
        Set user parameters on notification.
        """
        if id:
            self.user["id"] = id
        if name:
            self.user["name"] = name
        if email:
            self.user["email"] = email

    def add_custom_data(self, key, value):
        """
        Add data to the "custom" tag of Bugsnag
        """
        self.add_tab("custom", {key: value})

    def add_tab(self, name, dictionary):
        """
        Add a meta-data tab to the notification

        If the tab already exists, the new content will be merged into the
        existing content.
        """
        if not isinstance(dictionary, dict):
            self.add_tab("custom", {name: dictionary})
            return

        if name not in self.meta_data:
            self.meta_data[name] = {}

        self.meta_data[name].update(dictionary)

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
        user_exclude_modules = self.config.get("traceback_exclude_modules")
        for exclude_module in user_exclude_modules:
            try:
                module_file = exclude_module.__file__
                if module_file[-4:] == '.pyc':
                    module_file = module_file[:-1]
                exclude_module_paths.append(module_file)
            except Exception:
                bugsnag.logger.exception(
                    'Could not exclude module: %s' % repr(exclude_module))

        lib_root = self.config.get("lib_root")
        if lib_root and lib_root[-1] != os.sep:
            lib_root += os.sep

        project_root = self.config.get("project_root")
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
                "code": self._code_for(file_name, int(str(line[1])))
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
        filters = self.config.params_filters
        encoder = SanitizingJSONEncoder(separators=(',', ':'),
                                        keyword_filters=filters)
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
                "appVersion": self.app_version,
                "context": self.context,
                "groupingHash": self.grouping_hash,
                "exceptions": [{
                    "errorClass": class_name(self.exception),
                    "message": self.exception,
                    "stacktrace": self.stacktrace,
                }],
                "metaData": FilterDict(self.meta_data),
                "user": FilterDict(self.user),
                "device": FilterDict({
                    "hostname": self.hostname
                }),
                "projectRoot": self.config.get("project_root"),
                "libRoot": self.config.get("lib_root"),
                "session": self.session
            }]
        })
