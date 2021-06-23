from webob import Request
import sys
from typing import Dict

import bugsnag
from bugsnag.wsgi import request_path
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.legacy import _auto_leave_breadcrumb
from bugsnag.utils import sanitize_url

# Attempt to import bottle for runtime version report, but only if already
# in use in app
bottle_present = False
if 'bottle' in sys.modules:
    bottle_present = True
    try:
        import bottle
    except ImportError:
        bottle_present = False


__all__ = ('BugsnagMiddleware',)


def add_wsgi_request_data_to_notification(event):
    if not hasattr(event.request_config, "wsgi_environ"):
        return

    environ = event.request_config.wsgi_environ
    request = Request(environ)
    event.request = request
    path = request_path(environ)

    event.context = "%s %s" % (request.method, path)
    event.set_user(id=request.client_addr)
    event.add_tab("request", {
        "url": "%s%s" % (request.application_url, path),
        "headers": dict(request.headers),
        "params": dict(request.params),
    })

    if bugsnag.configure().send_environment:
        event.add_tab("environment", dict(request.environ))


class WrappedWSGIApp:
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

            _auto_leave_breadcrumb(
                'http request',
                _get_breadcrumb_metadata(environ),
                BreadcrumbType.NAVIGATION
            )

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


def _get_breadcrumb_metadata(environ) -> Dict[str, str]:
    metadata = {}

    if 'PATH_INFO' in environ:
        metadata['to'] = environ['PATH_INFO']

    if 'HTTP_REFERER' in environ:
        metadata['from'] = sanitize_url(environ['HTTP_REFERER'])

    return metadata


class BugsnagMiddleware:
    """
    Notifies Bugsnag on any unhandled exception that happens while processing
    a request in your application.

    This middleware should be installed before any middlewares that catch
    the exception and render an error messae.
    """

    def __init__(self, application):
        middleware = bugsnag.configure().internal_middleware
        if bottle_present:
            bugsnag.configure().runtime_versions['bottle'] = bottle.__version__
        middleware.before_notify(add_wsgi_request_data_to_notification)
        self.application = application

    def __call__(self, environ, start_response):
        return WrappedWSGIApp(self.application, environ, start_response)
