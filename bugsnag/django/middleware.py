from __future__ import division, print_function, absolute_import

import bugsnag
import bugsnag.django

def is_development_server(request):
    server = request.META.get('wsgi.file_wrapper', None)

    if server is None:
        return False

    return server.__module__ == 'django.core.servers.basehttp'

class BugsnagMiddleware(object):
    def __init__(self):
        bugsnag.django.configure()

    # pylint: disable-msg=R0201
    def process_request(self, request):
        if is_development_server(request):
            bugsnag.configure(release_stage="development")

        bugsnag.configure_request(django_request=request)

        return None

    # pylint: disable-msg=W0613
    def process_response(self, request, response):
        bugsnag.clear_request_config()

        return response

    def process_exception(self, request, exception):
        try:
            bugsnag.auto_notify(exception)

        except Exception as exc:
            bugsnag.log("Error in exception middleware: %s" % exc)

        bugsnag.clear_request_config()

        return None
