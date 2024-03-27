from uuid import uuid4
from threading import Lock
from typing import Callable


class RequestTracker:
    def __init__(self):
        self._mutex = Lock()
        self._requests = set()  # type: set[str]

    def new_request(self) -> Callable[[], None]:
        """
        Track a new request, returning a callback that marks the request as
        complete.

        >>> request_tracker = RequestTracker()
        >>> mark_request_complete = request_tracker.new_request()
        >>> # ...make the request...
        >>> mark_request_complete()
        """
        request_id = uuid4().hex

        with self._mutex:
            self._requests.add(request_id)

        def mark_request_complete():
            with self._mutex:
                # we use 'discard' instead of 'remove' to allow this callback
                # to be called multiple times without raising an error
                self._requests.discard(request_id)

        return mark_request_complete

    def has_in_flight_requests(self) -> bool:
        """
        See if there are any requests that have not been marked as completed.

        >>> request_tracker = RequestTracker()
        >>> request_tracker.has_in_flight_requests()
        False
        >>> mark_request_complete = request_tracker.new_request()
        >>> request_tracker.has_in_flight_requests()
        True
        >>> mark_request_complete()
        >>> request_tracker.has_in_flight_requests()
        False
        """
        with self._mutex:
            return bool(self._requests)
