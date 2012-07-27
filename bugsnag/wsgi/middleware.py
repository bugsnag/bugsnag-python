import sys
import urllib

# TODO:JS
# Fill in the basics (https://github.com/dcramer/raven/blob/master/raven/utils/wsgi.py)

class BugsnagMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):       
        try:
            for event in self.app(environ, start_response):
                yield event
        except Exception, e:
            self.handle_exception(exc_info, environ)
            exc_info = None
            raise

    def handle_exception(self, exception, env):
        path = ""
        path.append(urllib.quote(env.get('SCRIPT_NAME', '').rstrip('/')))
        path.append(urllib.quote('/' + env.get('PATH_INFO', '').lstrip('/')))

        bugsnag.configure_request(
            context=path,
            request_data={
                'path': path,
                'params': "TODO",
                'url': "TODO",
            },
            environment_data=dict(env),
        )
        
        bugsnag.auto_notify(exception)