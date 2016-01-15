from flask import got_request_exception, request, session

import bugsnag
from bugsnag.wsgi import request_path


def add_flask_request_to_notification(notification):
    if not request:
        return

    notification.context = "%s %s" % (request.method,
                                      request_path(request.environ))

    if 'id' not in notification.user:
        notification.set_user(id=request.remote_addr)
    notification.add_tab("session", dict(session))
    notification.add_tab("environment", dict(request.environ))
    notification.add_tab("request", {
        "url": request.base_url,
        "headers": dict(request.headers),
        "params": dict(request.form),
        "data": request.get_json() or dict(body=request.data)
    })


def handle_exceptions(app):
    bugsnag.before_notify(add_flask_request_to_notification)
    got_request_exception.connect(__log_exception, app)


# pylint: disable-msg=W0613
def __log_exception(sender, exception, **extra):
    bugsnag.auto_notify(exception)
