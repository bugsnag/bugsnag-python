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
    notification = Notification(Exception("oops"), config, {"request_data":{"arguments":{"password":"supersecret"}}})

    payload = json.loads(notification._generate_payload())

    assert(payload['events'][0]['metaData']['request']['arguments']['password'] == '[FILTERED]')
