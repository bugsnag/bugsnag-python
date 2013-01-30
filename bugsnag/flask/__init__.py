import urlparse

from flask import got_request_exception, request, session
import bugsnag

def handle_exceptions(app):
    got_request_exception.connect(__log_exception, app)

def __log_exception(sender, exception, **extra):
    bugsnag.configure_request(
        context="%s %s" % (request.method, request.path),
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