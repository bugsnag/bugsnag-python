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
from bugsnag.utils import sanitize_object
from bugsnag.utils import fully_qualified_class_name as class_name
from bugsnag.utils import package_version


def request(req):
    try:
        resp = urllib2.urlopen(req)
        status = resp.getcode()

        if status != 200:
            bugsnag.log("Notification to %s failed, status %d" % status)

    except Exception:
        bugsnag.log("Notification to %s failed" % (req.get_full_url()))
        print traceback.format_exc()


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
        url = self.config.get_endpoint()

        try:
            if self.config.api_key is None:
                bugsnag.log("No API key configured, couldn't notify")
                return

            # Return early if we shouldn't notify for current release stage
            if not self.config.should_notify():
                return

            # Return early if we should ignore exceptions of this type
            if self.config.should_ignore(self.exception):
                return

            # Generate the payload and make the request
            bugsnag.log("Notifying %s of exception" % url)

            payload = self.__generate_payload()
            req = urllib2.Request(url, payload, {
                'Content-Type': 'application/json'
            })
            threading.Thread(target=request, args=(req,)).start()

        except Exception:
            exc = traceback.format_exc()
            bugsnag.warn("Notification to %s failed:\n%s" % (url, exc))

    def __generate_payload(self):
        try:
            # Set up the lib root
            lib_root = self.config.get("lib_root", self.options)
            if lib_root and lib_root[-1] != os.sep:
                lib_root += os.sep

            # Set up the project root
            project_root = self.config.get("project_root", self.options)
            if project_root and project_root[-1] != os.sep:
                project_root += os.sep

            # Build the stacktrace
            tb = self.options.get("traceback", sys.exc_info()[2])
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
            notifier_version = package_version("bugsnag_python") or "unknown"

            # Construct the payload dictionary
            payload = {
                "apiKey": self.config.api_key,
                "notifier": {
                    "name": self.NOTIFIER_NAME,
                    "url": self.NOTIFIER_URL,
                    "version": notifier_version,
                },
                "events": [{
                    "releaseStage": self.config.get("release_stage", self.options),
                    "appVersion": self.config.get("app_version", self.options),
                    "context": self.request_config.get("context", self.options),
                    "userId": self.request_config.get("user_id", self.options),
                    "exceptions": [{
                        "errorClass": class_name(self.exception),
                        "message": str(self.exception),
                        "stacktrace": stacktrace,
                    }],
                    "metaData": self.__generate_metadata(),
                }]
            }

            # JSON-encode and return the payload
            return json.dumps(payload)
        finally:
            del tb

    def __generate_metadata(self):
        return {
            "request": sanitize_object(
                self.request_config.get("request_data", self.options)
            ),
            "environment": sanitize_object(
                self.request_config.get("environment_data", self.options)
            ),
            "session": sanitize_object(
                self.request_config.get("session_data", self.options)
            ),
            "extraData": sanitize_object(
                self.request_config.get("extra_data", self.options)
            ),
        }
