import flask
from typing import Dict

import bugsnag
from bugsnag.wsgi import request_path
from bugsnag.legacy import _auto_leave_breadcrumb
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.utils import remove_query_from_url


__all__ = ('handle_exceptions',)


def add_flask_request_to_notification(event: bugsnag.Event):
    if not flask.request:
        return

    event.request = flask.request
    if event.context is None:
        event.context = "%s %s" % (flask.request.method,
                                   request_path(flask.request.environ))

    if "id" not in event.user:
        event.set_user(id=flask.request.remote_addr)
    event.add_tab("session", dict(flask.session))
    if bugsnag.configure().send_environment:
        event.add_tab("environment", dict(flask.request.environ))
    event.add_tab("request", {
        "url": flask.request.base_url,
        "headers": dict(flask.request.headers),
        "params": dict(flask.request.form),
        "data":
            flask.request.get_json(silent=True) or
            dict(body=flask.request.data)
    })


def handle_exceptions(app):
    middleware = bugsnag.configure().internal_middleware
    bugsnag.configure().runtime_versions['flask'] = flask.__version__
    middleware.before_notify(add_flask_request_to_notification)
    flask.got_request_exception.connect(__log_exception, app)
    flask.request_started.connect(_on_request_started, app)


# pylint: disable-msg=W0613
def __log_exception(sender, exception, **extra):
    bugsnag.auto_notify(exception, severity_reason={
        "type": "unhandledExceptionMiddleware",
        "attributes": {
            "framework": "Flask"
        }
    })


def _on_request_started(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()

    if flask.request:
        _auto_leave_breadcrumb(
            'http request',
            _get_breadcrumb_metadata(flask.request),
            BreadcrumbType.NAVIGATION
        )


def _get_breadcrumb_metadata(request) -> Dict[str, str]:
    metadata = {'to': request_path(request.environ)}

    if 'referer' in request.headers:
        metadata['from'] = remove_query_from_url(request.headers['referer'])

    return metadata
