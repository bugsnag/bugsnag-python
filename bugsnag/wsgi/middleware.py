import sys
import urllib

import bugsnag

class BugsnagMiddleware(object):
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):       
        try:
            iterable = self.application(environ, start_response)
        except Exception as e:
            self.handle_exception(e, environ)
            raise

        try:
            for event in iterable:
                yield event
        except Exception as e:
            self.handle_exception(e, environ)
            raise
        finally:
            if iterable and hasattr(iterable, 'close') and callable(iterable.close):
                try:
                    iterable.close()
                except Exception:
                    self.handle_exception(e, environ)

    def handle_exception(self, exception, env):
        bugsnag.configure_request(
            context="%s %s" % (env.get('REQUEST_METHOD', ''), env.get('PATH_INFO', '')),
            request_data= {
                'url': get_current_url(env),
                'httpMethod': env.get('REQUEST_METHOD', ''),
                'params': "TODO",
                'ip': "TODO",
                'userAgent': "TODO",
            },
            environment_data=dict(env),
        )
        bugsnag.auto_notify(exception)
        bugsnag.clear_request_config()


def get_host(environ):
    scheme = environ.get('wsgi.url_scheme')
    if 'HTTP_X_FORWARDED_HOST' in environ:
        result = environ['HTTP_X_FORWARDED_HOST']
    elif 'HTTP_HOST' in environ:
        result = environ['HTTP_HOST']
    else:
        result = environ['SERVER_NAME']
        if (scheme, str(environ['SERVER_PORT'])) not \
           in (('https', '443'), ('http', '80')):
            result += ':' + environ['SERVER_PORT']
    if result.endswith(':80') and scheme == 'http':
        result = result[:-3]
    elif result.endswith(':443') and scheme == 'https':
        result = result[:-4]
    return result

def get_current_url(environ):
    tmp = [environ['wsgi.url_scheme'], '://', get_host(environ)]
    tmp.append(urllib.quote(environ.get('SCRIPT_NAME', '').rstrip('/')))
    tmp.append(urllib.quote('/' + environ.get('PATH_INFO', '').lstrip('/')))
    return ''.join(tmp)