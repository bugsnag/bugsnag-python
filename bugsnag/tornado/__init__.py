from tornado.web import RequestHandler
import bugsnag


class BugsnagRequestHandler(RequestHandler):
    def _handle_request_exception(self, exc):
        # Set the request info
        bugsnag.configure_request(
            user_id=self.request.remote_ip,
            context=self._get_context(),
            request_data={
                "url": self.request.full_url(),
                "method": self.request.method,
                "arguments": self.request.arguments,
            },
        )

        # Notify bugsnag
        bugsnag.notify(exc)

        # Call the parent handler
        RequestHandler._handle_request_exception(self, exc)

    def _get_context(self):
        return "%s %s" % (self.request.method, self.request.uri.split('?')[0])
