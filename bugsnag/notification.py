import os
import urllib2
import sys
import threading
import traceback

try:
    import json
except ImportError:
    import simplejson as json

import bugsnag
from bugsnag.utils import sanitize_object, fully_qualified_class_name


class Notification(object):
    """
    A single exception notification to Bugsnag.
    """
    NOTIFIER_NAME = "Python Bugsnag Notifier"
    NOTIFIER_URL = "https://github.com/bugsnag/bugsnag-python"

    def __init__(self, exception, config, request_config, **options):
        self.exception = exception
        self.options = options
        self.config = config
        self.request_config = request_config

    def deliver(self):
        """
        Deliver the exception notification to Bugsnag.
        """
        try:
            if self.config.api_key is None:
                bugsnag.log("No API key configured, couldn't notify")
                return

            if self.config.notify_release_stages is not None and self.config.release_stage not in self.config.notify_release_stages:
                return

            if self.config.ignore_classes is not None and fully_qualified_class_name(self.exception) in self.config.ignore_classes:
                return

            # Generate the URL
            if self.config.use_ssl:
                url = "https://%s" % self.config.endpoint
            else:
                url = "http://%s" % self.config.endpoint

            bugsnag.log("Notifying %s of exception" % url)

            # Generate the payload
            payload = self.__generate_payload(self.exception, **self.options)

            req = urllib2.Request(url, payload, {
                'Content-Type': 'application/json'
            })
            threading.Thread(target=self.__open_url, args=(req,)).start()

        except Exception, exc:
            bugsnag.warn("Notification to %s failed:\n%s" % (url, traceback.format_exc()))

    def __generate_payload(self, exception, **options):
        try:
            # Set up the lib root
            lib_root = self.config.get("lib_root", options)
            if lib_root and lib_root[-1] != os.sep:
                lib_root += os.sep

            # Set up the project root
            project_root = self.config.get("project_root", options)
            if project_root and project_root[-1] != os.sep:
                project_root += os.sep

            # Build the stacktrace
            tb = options.get("traceback", sys.exc_info()[2])
            if tb:
                trace = traceback.extract_tb(tb)
            else:
                trace = traceback.extract_stack()

            bugsnag_module_path = os.path.dirname(bugsnag.__file__)

            stacktrace = []
            for line in trace:
                file_name = os.path.abspath(str(line[0]))
                in_project = False

                if file_name.startswith(bugsnag_module_path):
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
                })

            stacktrace.reverse()

            # Fetch the notifier version from the package
            notifier_version = "unknown"
            try:
                import pkg_resources
                notifier_version = pkg_resources.get_distribution("bugsnag_python").version
            except:
                pass

            # Construct the payload dictionary
            payload = {
                "apiKey": self.config.api_key,
                "notifier": {
                    "name": self.NOTIFIER_NAME,
                    "url": self.NOTIFIER_URL,
                    "version": notifier_version,
                },
                "events": [{
                    "releaseStage": self.config.get("release_stage", options),
                    "appVersion": self.config.get("app_version", options),
                    "context": self.request_config.get("context", options),
                    "userId": self.request_config.get("user_id", options),
                    "exceptions": [{
                        "errorClass": fully_qualified_class_name(self.exception),
                        "message": str(self.exception),
                        "stacktrace": stacktrace,
                    }],
                    "metaData": {
                        "request": sanitize_object(self.request_config.get("request_data", options)),
                        "environment": sanitize_object(self.request_config.get("environment_data", options)),
                        "session": sanitize_object(self.request_config.get("session_data", options)),
                        "extraData": sanitize_object(self.request_config.get("extra_data", options)),
                    }
                }]
            }

            # JSON-encode and return the payload
            return json.dumps(payload)
        finally:
            del tb

    def __open_url(self, req):
        try:
            resp = urllib2.urlopen(req)
            status = resp.getcode()

            if status != 200:
                bugsnag.log("Notification to %s failed, got non-200 response code %d" % status)
        except Exception, e:
            bugsnag.log("Notification to %s failed" % (req.get_full_url()))
            print traceback.format_exc()
