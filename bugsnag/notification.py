import os
import urllib2
import sys
import threading
import traceback
import inspect

try:
    import json
except ImportError:
    import simplejson as json

import bugsnag

class Notification(object):
    """
    A single exception notification to Bugsnag.
    """
    MAX_STRING_LENGTH = 1024

    NOTIFIER_NAME = "Python Bugsnag Notifier"
    NOTIFIER_URL = "https://github.com/bugsnag/bugsnag-python"

    def __init__(self, exception, configuration, request_configuration, **options):
        self.exception = exception
        self.options = options
        self.configuration = configuration
        self.request_configuration = request_configuration

    def deliver(self):
        """
        Deliver the exception notification to Bugsnag.
        """
        try:
            if self.configuration.api_key == None:
                bugsnag.log("No API key configured, couldn't notify")
                return
            
            if self.configuration.notify_release_stages != None and not self.configuration.release_stage in self.configuration.notify_release_stages:
                return
        
            if self.configuration.ignore_classes != None and self.__fully_qualified_class_name(self.exception) in self.configuration.ignore_classes:
                return

            # Generate the URL
            if self.configuration.use_ssl:
                url = "https://%s" % self.configuration.endpoint
            else:
                url = "http://%s" % self.configuration.endpoint

            bugsnag.log("Notifying %s of exception" % url)

            # Generate the payload
            payload = self.__generate_payload(self.exception, **self.options)
        
            req = urllib2.Request(url, payload, {
                'Content-Type': 'application/json'
            })
            threading.Thread(target=self.__open_url, args=(req,)).start()
        
        except Exception, exc:
            bugsnag.log("Notification to %s failed, %s" % (url, exc))

    def __generate_payload(self, exception, **options):
        try:
            # Set up the lib root
            lib_root = self.configuration.get("lib_root", options)
            if lib_root and lib_root[-1] != os.sep:
                lib_root += os.sep

            # Set up the project root
            project_root = self.configuration.get("project_root", options)
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
            except: pass

            # Construct the payload dictionary
            payload = {
                "apiKey": self.configuration.api_key,
                "notifier": {
                    "name": self.NOTIFIER_NAME,
                    "url": self.NOTIFIER_URL,
                    "version": notifier_version,
                },
                "events": [{
                    "releaseStage": self.configuration.get("release_stage", options),
                    "appVersion": self.configuration.get("app_version", options),
                    "context": self.request_configuration.get("context", options),
                    "userId": self.request_configuration.get("user_id", options),
                    "exceptions": [{
                        "errorClass": self.__fully_qualified_class_name(self.exception),
                        "message": str(self.exception),
                        "stacktrace": stacktrace,
                    }],
                    "metaData": {
                        "request": self.__sanitize_dict(self.request_configuration.get("request_data", options)),
                        "environment": self.__sanitize_dict(self.request_configuration.get("environment_data", options)),
                        "session": self.__sanitize_dict(self.request_configuration.get("session_data", options)),
                        "extraData": self.__sanitize_dict(self.request_configuration.get("extra_data", options)),
                    }
                }]
            }

            # JSON-encode and return the payload
            return json.dumps(payload)
        finally:
            del tb

    def __fully_qualified_class_name(self, obj):
        module = inspect.getmodule(obj)
        if module != None and module.__name__ != "__main__":
            return module.__name__ + "." + obj.__class__.__name__
        else:
            return obj.__class__.__name__

    def __sanitize_dict(self, dictionary):
        for k,v in dictionary.iteritems():
            if k in self.configuration.params_filters:
                del dictionary[k]
            elif isinstance(v,dict):
                self.__sanitize_dict(v)
            else:
                dictionary[k] = str(v)[:self.MAX_STRING_LENGTH]
        return dictionary

    def __open_url(self, req):
        try:
            resp = urllib2.urlopen(req)
            status = resp.getcode()

            if status != 200:
                bugsnag.log("Notification to %s failed, got non-200 response code %d" % status)
        except Exception, e:
            bugsnag.log("Notification to %s failed, %s" % (req.get_full_url(), e))
