import pytest

from bugsnag import Configuration, Notification, RequestConfiguration
from tests.test_event import TestEvent


def test_create_notification_warns():
    config = Configuration()
    req_config = RequestConfiguration.get_instance()
    with pytest.warns(DeprecationWarning) as record:
        _ = Notification(Exception('shucks'), config, req_config)
        assert len(record) == 1
        message = str(record[0].message)
        assert message == ('The Notification class has been deprecated in ' +
                           'favor of bugsnag.event.Event and will be ' +
                           'removed in a future release.')


@pytest.mark.filterwarnings("ignore:The Notification class")
class TestNotification(TestEvent):
    event_class = Notification
