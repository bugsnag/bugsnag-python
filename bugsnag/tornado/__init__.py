import tornado
from tornado.web import RequestHandler, HTTPError
from tornado.wsgi import WSGIContainer
from typing import Dict, Any
from urllib.parse import parse_qs
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.utils import is_json_content_type, sanitize_url
from bugsnag.legacy import _auto_leave_breadcrumb
import bugsnag
import json


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
            'url': self.request.full_url(),
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
            env = WSGIContainer.environ(self.request)
            event.add_tab("environment", env)

    def _handle_request_exception(self, exc: BaseException):
        options = {
            "user": {"id": self.request.remote_ip},
            "context": self._get_context(),
            "request": {
                "url": self.request.full_url(),
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
            metadata['from'] = sanitize_url(self.request.headers['Referer'])

        return metadata

    def _get_context(self):
        return "%s %s" % (self.request.method, self.request.uri.split("?")[0])

    def bugsnag_ignore_status_codes(self):
        # Subclasses can override to add or remove codes
        return range(400, 500)
