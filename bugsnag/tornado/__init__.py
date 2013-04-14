from tornado.web import RequestHandler
import bugsnag

class BugsnagRequestHandler(RequestHandler):
    def _handle_request_exception(self, e):
        # Set the request info
        bugsnag.configure_request(
            user_id = self.request.remote_ip,
            context = "%s %s" % (self.request.method, self.request.uri.split('?')[0]),
            request_data = {
                "url": self.request.full_url(),
                "method": self.request.method,
                "arguments": self.request.arguments,
            },
        )

        # Notify bugsnag
        bugsnag.notify(e)

        # Call the parent handler
        RequestHandler._handle_request_exception(self, e)