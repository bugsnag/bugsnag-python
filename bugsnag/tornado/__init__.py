from tornado.web import RequestHandler
from tornado.web import HTTPError

import bugsnag


class BugsnagRequestHandler(RequestHandler):
    def _handle_request_exception(self, exc):

        options = {
            "user": {"id": self.request.remote_ip},
            "context": self._get_context(),
            "request": {
                "url": self.request.full_url(),
                "method": self.request.method,
                "arguments": self.request.arguments,
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

    def _get_context(self):
        return "%s %s" % (self.request.method, self.request.uri.split('?')[0])

    def bugsnag_ignore_status_codes(self):
        # Subclasses can override to add or remove codes
        return range(400, 500)
