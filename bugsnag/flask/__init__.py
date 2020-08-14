import flask

import bugsnag
from bugsnag.wsgi import request_path


def add_flask_request_to_notification(notification):
    if not flask.request:
        return

    if notification.context is None:
        notification.context = "%s %s" % (flask.request.method,
                                          request_path(flask.request.environ))

    if "id" not in notification.user:
        notification.set_user(id=flask.request.remote_addr)
    notification.add_tab("session", dict(flask.session))
    if bugsnag.configure().send_environment:
        notification.add_tab("environment", dict(flask.request.environ))
    notification.add_tab("request", {
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
    flask.request_started.connect(__track_session, app)


# pylint: disable-msg=W0613
def __log_exception(sender, exception, **extra):
    bugsnag.auto_notify(exception, severity_reason={
        "type": "unhandledExceptionMiddleware",
        "attributes": {
            "framework": "Flask"
        }
    })


def __track_session(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()
