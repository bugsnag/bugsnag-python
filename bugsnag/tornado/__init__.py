import tornado
from tornado.web import RequestHandler, HTTPError
from typing import Dict, Any  # noqa
from urllib.parse import parse_qs, unquote_to_bytes
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.context import create_new_context
from bugsnag.utils import (
    is_json_content_type,
    remove_query_from_url,
    sanitize_url
)
from bugsnag.legacy import _auto_leave_breadcrumb
import bugsnag
import json


def tornado_environ(request):
    """Copyright The Tornado Web Library Authors

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Converts a tornado request to a WSGI environment.

    Taken from tornado's WSGI implementation
    https://github.com/tornadoweb/tornado/blob/6e3521da44c349197cf8048c8a6c69d3f4ccd971/tornado/wsgi.py#L207-L246
    but without WSGI prefixed entries that require a WSGI application.
    """
    hostport = request.host.split(":")
    if len(hostport) == 2:
        host = hostport[0]
        port = int(hostport[1])
    else:
        host = request.host
        port = 443 if request.protocol == "https" else 80
    environ = {
        "REQUEST_METHOD": request.method,
        "SCRIPT_NAME": "",
        "PATH_INFO": unquote_to_bytes(request.path).decode("latin1"),
        "QUERY_STRING": request.query,
        "REMOTE_ADDR": request.remote_ip,
        "SERVER_NAME": host,
        "SERVER_PORT": str(port),
        "SERVER_PROTOCOL": request.version,
    }
    if "Content-Type" in request.headers:
        environ["CONTENT_TYPE"] = request.headers.pop("Content-Type")
    if "Content-Length" in request.headers:
        environ["CONTENT_LENGTH"] = request.headers.pop("Content-Length")
    for key, value in request.headers.items():
        environ["HTTP_" + key.replace("-", "_").upper()] = value
    return environ


class BugsnagRequestHandler(RequestHandler):
    def add_tornado_request_to_notification(self, event: bugsnag.Event):
        if not hasattr(self, "request"):
            return

        event.request = self.request
        request_tab = {
            'method': self.request.method,
            'path': self.request.path,
            'GET': parse_qs(self.request.query),
            'POST': {},
            'url': sanitize_url(self.request.full_url(), event.config),
        }  # type: Dict[str, Any]
        try:
            if (len(self.request.body) > 0):
                headers = self.request.headers
                body = self.request.body.decode('utf-8', 'replace')
                is_json = is_json_content_type(headers.get('Content-Type', ''))
                if is_json and request_tab["method"] == "POST":
                    request_tab["POST"] = json.loads(body)
                else:
                    request_tab["POST"] = self.request.body_arguments
        except Exception:
            pass

        event.add_tab("request", request_tab)

        if bugsnag.configure().send_environment:
            env = tornado_environ(self.request)
            event.add_tab("environment", env)

    def _handle_request_exception(self, exc: BaseException):
        options = {
            "user": {"id": self.request.remote_ip},
            "context": self._get_context(),
            "request": {
                "url": sanitize_url(
                    self.request.full_url(),
                    bugsnag.configuration
                ),
                "method": self.request.method,
                "arguments": self.request.arguments,
            },
            "severity_reason": {
                "type": "unhandledExceptionMiddleware",
                "attributes": {
                    "framework": "Tornado"
                }
            }
        }

        # Notify bugsnag, unless it's an HTTPError that we specifically want
        # to ignore
        should_notify_bugsnag = True
        if isinstance(exc, HTTPError):
            ignore_status_codes = self.bugsnag_ignore_status_codes()
            if ignore_status_codes and exc.status_code in ignore_status_codes:
                should_notify_bugsnag = False

        if should_notify_bugsnag:
            bugsnag.auto_notify(exc, **options)

        # Call the parent handler
        RequestHandler._handle_request_exception(self, exc)  # type: ignore

    def prepare(self):
        middleware = bugsnag.configure().internal_middleware
        bugsnag.configure().runtime_versions['tornado'] = tornado.version
        middleware.before_notify(self.add_tornado_request_to_notification)
        bugsnag.configure()._breadcrumbs.create_copy_for_context()
        create_new_context()

        _auto_leave_breadcrumb(
            'http request',
            self._get_breadcrumb_metadata(),
            BreadcrumbType.NAVIGATION
        )

        if bugsnag.configuration.auto_capture_sessions:
            bugsnag.start_session()

    def _get_breadcrumb_metadata(self) -> Dict[str, str]:
        if not hasattr(self, 'request'):
            return {}

        metadata = {'to': self.request.path}

        if 'Referer' in self.request.headers:
            metadata['from'] = remove_query_from_url(
                self.request.headers['Referer']
            )

        return metadata

    def _get_context(self):
        return "%s %s" % (self.request.method, self.request.uri.split("?")[0])

    def bugsnag_ignore_status_codes(self):
        # Subclasses can override to add or remove codes
        return range(400, 500)
