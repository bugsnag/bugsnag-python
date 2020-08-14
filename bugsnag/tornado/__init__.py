import tornado
from tornado.web import RequestHandler
from tornado.web import HTTPError
from six.moves import urllib
from bugsnag.utils import is_json_content_type
import bugsnag
import json


class BugsnagRequestHandler(RequestHandler):
    def add_tornado_request_to_notification(self, notification):
        if not hasattr(self, "request"):
            return

        request_tab = {
            'method': self.request.method,
            'path': self.request.path,
            'GET': urllib.parse.parse_qs(self.request.query),
            'POST': {},
            'url': self.request.full_url(),
        }
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

        notification.add_tab("request", request_tab)

        if bugsnag.configure().send_environment:
            env = tornado.wsgi.WSGIContainer.environ(self.request)
            notification.add_tab("environment", env)

    def _handle_request_exception(self, exc):
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
        if type(exc) == HTTPError:
            ignore_status_codes = self.bugsnag_ignore_status_codes()
            if ignore_status_codes and exc.status_code in ignore_status_codes:
                should_notify_bugsnag = False

        if should_notify_bugsnag:
            bugsnag.auto_notify(exc, **options)

        # Call the parent handler
        RequestHandler._handle_request_exception(self, exc)

    def prepare(self):
        middleware = bugsnag.configure().internal_middleware
        bugsnag.configure().runtime_versions['tornado'] = tornado.version
        middleware.before_notify(self.add_tornado_request_to_notification)

        if bugsnag.configuration.auto_capture_sessions:
            bugsnag.start_session()

    def _get_context(self):
        return "%s %s" % (self.request.method, self.request.uri.split("?")[0])

    def bugsnag_ignore_status_codes(self):
        # Subclasses can override to add or remove codes
        return range(400, 500)
