from werkzeug.wrappers import Request

import bugsnag
import urllib


def handle_exception(exception, env):
    request = Request(env)

    # Don't use werkzeug to get the path, it does zany stuff with unicode
    path = urllib.quote('/' + env.get('PATH_INFO', '').lstrip('/'))

    bugsnag.configure_request(
        context="%s %s" % (request.method, path),
        user_id=request.remote_addr,
        request_data={
            "url": request.base_url,
            "headers": dict(request.headers),
            "cookies": dict(request.cookies),
            "params": dict(request.form),
        },
        environment_data=dict(request.environ),
    )
    bugsnag.auto_notify(exception)
    bugsnag.clear_request_config()


class BugsnagMiddleware(object):
    """
    Bugsnag middleware bitches
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        try:
            iterable = self.application(environ, start_response)
        except Exception as e:
            handle_exception(e, environ)
            raise

        try:
            for event in iterable:
                yield event
        except Exception as e:
            handle_exception(e, environ)
            raise
        finally:
            if iterable and hasattr(iterable, 'close') and \
               callable(iterable.close):

                try:
                    iterable.close()
                except Exception:
                    handle_exception(e, environ)
