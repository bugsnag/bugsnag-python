from flask import got_request_exception, request, session

import bugsnag
from bugsnag.wsgi import request_path


def handle_exceptions(app):
    got_request_exception.connect(__log_exception, app)


# pylint: disable-msg=W0613
def __log_exception(sender, exception, **extra):
    bugsnag.configure_request(
        context="%s %s" % (request.method, request_path(request.environ)),
        user_id=request.remote_addr,
        request_data={
            "url": request.base_url,
            "headers": dict(request.headers),
            "cookies": dict(request.cookies),
            "params": dict(request.form),
        },
        session_data=dict(session),
        environment_data=dict(request.environ),
    )

    bugsnag.auto_notify(exception)

    bugsnag.clear_request_config()
