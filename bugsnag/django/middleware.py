import bugsnag
import bugsnag.django

def get_user_id(request):
    return request.META['REMOTE_ADDR']


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

        try:
            bugsnag.configure_request(
                context=request.path,
                user_id=get_user_id(request),
                session_data=dict(request.session),
                request_data={
                    'path': request.path,
                    'encoding': request.encoding,
                    'params': dict(request.REQUEST),
                    'url': request.build_absolute_uri(),
                },
                environment_data=dict(request.META),
            )

        except Exception as exc:
            bugsnag.log("Error in request middleware: %s" % exc)

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
