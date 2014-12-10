from bugsnag.configuration import Configuration
from bugsnag.notification import Notification
import fixtures

import os
import socket
import json
import inspect

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

def test_code():
    """
        It should include code
    """
    config = Configuration()
    line = inspect.currentframe().f_lineno + 1
    notification = Notification(Exception("oops"), config, {})

    payload = notification._payload()

    code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']

    assert(code[line - 3] == "    \"\"\"")
    assert(code[line - 2] == "    config = Configuration()")
    assert(code[line - 1] == "    line = inspect.currentframe().f_lineno + 1")
    assert(code[line + 0] == "    notification = Notification(Exception(\"oops\"), config, {})" )
    assert(code[line + 1] == "")
    assert(code[line + 2] == "    payload = notification._payload()")
    assert(code[line + 3] == "")

def test_code_at_start_of_file():

    config = Configuration()
    line = inspect.currentframe().f_lineno + 1
    notification = Notification(fixtures.start_of_file[1], config, {}, traceback=fixtures.start_of_file[2])

    payload = notification._payload()

    code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']
    assert({1: 'try:', 2: '    import sys; raise Exception("start")', 3: 'except Exception, e: start_of_file = sys.exc_info()', 4: '# 4', 5: '# 5', 6: '# 6', 7: '# 7'} == code)

def test_code_at_end_of_file():

    config = Configuration()
    line = inspect.currentframe().f_lineno + 1
    notification = Notification(fixtures.end_of_file[1], config, {}, traceback=fixtures.end_of_file[2])

    payload = notification._payload()

    code = payload['events'][0]['exceptions'][0]['stacktrace'][0]['code']
    assert({5: '# 5', 6: '# 6', 7: '# 7', 8: '# 8', 9: 'try:', 10: '    import sys; raise Exception("end")', 11: 'except Exception, e: end_of_file = sys.exc_info()'} == code)
