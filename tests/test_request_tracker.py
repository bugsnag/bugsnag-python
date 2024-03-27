from bugsnag.request_tracker import RequestTracker


def test_a_request_can_be_tracked():
    tracker = RequestTracker()
    assert not tracker.has_in_flight_requests()

    tracker.new_request()
    assert tracker.has_in_flight_requests()


def test_a_request_can_be_marked_as_complete():
    tracker = RequestTracker()
    assert not tracker.has_in_flight_requests()

    complete_request = tracker.new_request()
    assert tracker.has_in_flight_requests()

    complete_request()
    assert not tracker.has_in_flight_requests()


def test_requests_can_be_marked_as_complete():
    tracker = RequestTracker()

    complete_request_1 = tracker.new_request()
    complete_request_2 = tracker.new_request()
    complete_request_3 = tracker.new_request()

    assert tracker.has_in_flight_requests()

    complete_request_1()
    complete_request_2()

    assert tracker.has_in_flight_requests()

    complete_request_3()
    assert not tracker.has_in_flight_requests()


def test_callbacks_can_be_called_multiple_times():
    tracker = RequestTracker()
    assert not tracker.has_in_flight_requests()

    complete_request_1 = tracker.new_request()
    complete_request_2 = tracker.new_request()

    assert tracker.has_in_flight_requests()

    complete_request_1()
    complete_request_1()
    complete_request_1()

    assert tracker.has_in_flight_requests()

    complete_request_2()
    assert not tracker.has_in_flight_requests()

    complete_request_2()
    assert not tracker.has_in_flight_requests()
