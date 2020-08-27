import bugsnag

from bugsnag.wsgi.middleware import BugsnagMiddleware

bugsnag.configure(api_key="some-api-key")


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    raise Exception('Ack')
    return [b"Hello World"]


application = BugsnagMiddleware(application)
