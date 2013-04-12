from tornado.web import RequestHandler
import bugsnag

class BugsnagRequestHandler(RequestHandler):
    def _handle_request_exception(self, e):
        bugsnag.notify(e)
        tornado.web.RequestHandler._handle_request_exception(self, e)