from __future__ import division, print_function, absolute_import

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    from bugsnag.django.utils import MiddlewareMixin

import bugsnag
import bugsnag.django


class BugsnagMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        bugsnag.django.configure()
        super(BugsnagMiddleware, self).__init__(get_response)

    # pylint: disable-msg=R0201
    def process_request(self, request):
        bugsnag.configure_request(django_request=request)

        return None

    # pylint: disable-msg=W0613
    def process_response(self, request, response):
        bugsnag.clear_request_config()

        return response

    def process_exception(self, request, exception):
        try:
            bugsnag.auto_notify(
                exception,
                severity_reason={
                    "type": "unhandledExceptionMiddleware",
                    "attributes": {
                        "framework": "Django"
                    }
                }
            )

        except Exception:
            bugsnag.logger.exception("Error in exception middleware")

        bugsnag.clear_request_config()

        return None
