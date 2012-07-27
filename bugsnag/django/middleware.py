import bugsnag
from django.conf import settings
import django
import os

class BugsnagMiddleware(object):
    def __init__(self):
        django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
        
        bugsnag.configure(**django_bugsnag_settings)
    
    def process_request(self, request):
        try:
            server = request.META.get('wsgi.file_wrapper', None)
            if server is not None and server.__module__ == 'django.core.servers.basehttp':
                bugsnag.configure(release_stage="development")

            bugsnag.configure_request(
                context=request.path,
                user_id=request.user.username if request.user.is_authenticated() else request.META['REMOTE_ADDR'],
                session_data=dict(request.session),
                request_data={
                    'path': request.path,
                    'encoding': request.encoding,
                    'params': dict(request.REQUEST),
                    'url': request.build_absolute_uri(),
                },
                environment_data=dict(request.META),
            )
        except Exception, exc:
            bugsnag.log("Error in request middleware: %s" % exc)

        return None

    def process_response(self, request, response):
        bugsnag.clear_request_config()
        
        return response

    def process_exception(self, request, exception):
        try:
            bugsnag.auto_notify(exception)
        except Exception, exc:
            bugsnag.log("Error in exception middleware: %s" % exc)

        bugsnag.clear_request_config()

        return None