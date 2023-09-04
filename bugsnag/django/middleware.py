try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    from bugsnag.django.utils import MiddlewareMixin

from typing import Dict

import bugsnag
import bugsnag.django
from bugsnag.context import create_new_context
from bugsnag.legacy import _auto_leave_breadcrumb
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.utils import remove_query_from_url


class BugsnagMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.config = bugsnag.django.configure()
        super(BugsnagMiddleware, self).__init__(get_response)

    # pylint: disable-msg=R0201
    def process_request(self, request):
        bugsnag.configure_request(django_request=request)
        create_new_context()

        _auto_leave_breadcrumb(
            'http request',
            self._get_breadcrumb_metadata(request),
            BreadcrumbType.NAVIGATION
        )

        return None

    # pylint: disable-msg=W0613
    def process_response(self, request, response):
        self.config._breadcrumbs.clear()
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

            # ensure the 'got_request_exception' signal doesn't also notify
            # this exception
            setattr(exception, 'skip_bugsnag', True)

        except Exception:
            self.config.logger.exception("Error in exception middleware")

        bugsnag.clear_request_config()

        return None

    def _get_breadcrumb_metadata(self, request) -> Dict[str, str]:
        metadata = {'to': request.path}

        if 'HTTP_REFERER' in request.META:
            metadata['from'] = remove_query_from_url(
                request.META['HTTP_REFERER']
            )

        return metadata
