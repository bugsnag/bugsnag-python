try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    from bugsnag.django.utils import MiddlewareMixin

from typing import Dict
import asyncio
from asgiref.sync import sync_to_async


import bugsnag
import bugsnag.django
from bugsnag.legacy import _auto_leave_breadcrumb
from bugsnag.breadcrumbs import BreadcrumbType
from bugsnag.utils import remove_query_from_url


class BugsnagMiddleware(MiddlewareMixin):
    async_capable = True
    sync_capable = True

    def __init__(self, get_response=None):
        self.config = bugsnag.django.configure()
        self.get_response = get_response
        if asyncio.iscoroutinefunction(self.get_response):
            # Mark the class as async-capable, but do the actual switch
            # inside __call__ to avoid swapping out dunder methods
            self._is_coroutine = (
                asyncio.coroutines._is_coroutine  # type: ignore [attr-defined]
            )
        else:
            self._is_coroutine = None

        super(BugsnagMiddleware, self).__init__(get_response)

    def __call__(self, request):
        print("sync")
        # Exit out to async mode, if needed
        if self._is_coroutine:
            return self.__acall__(request)
        response = self.process_request(request)
        response = response or self.get_response(request)
        response = self.process_response(request, response)
        return response

    async def __acall__(self, request):
        print("async")
        """
        Async version of __call__ that is swapped in when an async request
        is running.
        """
        response = await sync_to_async(self.process_request)(request)
        response = response or await self.get_response(request)
        response = await sync_to_async(self.process_response)(request, response)
        return response

    # pylint: disable-msg=R0201
    def process_request(self, request):
        bugsnag.configure_request(django_request=request)

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