from webob import Request

import bugsnag
from bugsnag.wsgi import request_path


def add_wsgi_request_data_to_notification(notification):
    if not hasattr(notification.request_config, "wsgi_environ"):
        return

    environ = notification.request_config.wsgi_environ
    request = Request(environ)

    notification.context = "%s %s" % (request.method, request_path(environ))
    notification.set_user(id=request.remote_addr)
    notification.add_tab("request", {
        "url": request.path_url,
        "headers": dict(request.headers),
        "params": dict(request.params),
    })
    notification.add_tab("environment", dict(request.environ))


class WrappedWSGIApp(object):
    """
    Wraps a running WSGI app and sends all exceptions to bugsnag.
    """

    SEVERITY_REASON = {
        "type": "unhandledExceptionMiddleware",
        "attributes": {
            "framework": "WSGI"
        }
    }

    def __init__(self, application, environ, start_response):
        self.environ = environ

        bugsnag.configure_request(wsgi_environ=self.environ)

        try:
            if bugsnag.configuration.auto_capture_sessions:
                bugsnag.start_session()
            self.app = application(environ, start_response)
        except Exception as e:
            bugsnag.auto_notify(
                e,
                severity_reason=self.SEVERITY_REASON
            )
            raise

    def __iter__(self):
        try:
            for response in self.app:
                yield response

        except Exception as e:
            bugsnag.auto_notify(
                e,
                severity_reason=self.SEVERITY_REASON
            )
            raise

    def close(self):
        try:
            if hasattr(self.app, 'close'):
                return self.app.close()
        except Exception as e:
            bugsnag.auto_notify(
                e,
                severity_reason=self.SEVERITY_REASON
            )
            raise
        finally:
            bugsnag.clear_request_config()


class BugsnagMiddleware(object):
    """
    Notifies Bugsnag on any unhandled exception that happens while processing
    a request in your application.

    This middleware should be installed before any middlewares that catch
    the exception and render an error messae.
    """

    def __init__(self, application):
        middleware = bugsnag.configure().internal_middleware
        middleware.before_notify(add_wsgi_request_data_to_notification)
        self.application = application

    def __call__(self, environ, start_response):
        return WrappedWSGIApp(self.application, environ, start_response)
