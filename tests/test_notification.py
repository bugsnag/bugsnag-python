from bugsnag.configuration import Configuration
from bugsnag.notification import Notification
import os
import socket
import json

def test_sanitize():
    """
        It should sanitize request data
    """
    config = Configuration()
    notification = Notification(Exception("oops"), config, {}, request={"params":{"password":"secret"}})

    notification.add_tab("request", {"arguments":{"password":"secret"}})

    payload = notification._payload()

    assert(payload['events'][0]['metaData']['request']['arguments']['password'] == '[FILTERED]')
    assert(payload['events'][0]['metaData']['request']['params']['password'] == '[FILTERED]')
