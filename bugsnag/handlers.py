from __future__ import division, print_function, absolute_import

import logging
import bugsnag

class BugsnagHandler(logging.Handler):
    def __init__(self, api_key=None):
        super(BugsnagHandler, self).__init__()

        # Check if API key has been specified.
        if not bugsnag.configuration.api_key and not api_key:
            raise Exception, "API key has not been configured or specified"

        # If API key specified in logger, always use this value, even if another
        # value was configured previously
        if api_key:
            bugsnag.configuration.api_key = api_key

    def emit(self, record):
        if record.levelname.lower() in ['error', 'critical']:
            severity = 'error'
        elif record.levelname.lower() in ['warning', ]:
            severity = 'warning'
        else:
            severity = 'info'

        if record.exc_info:
            bugsnag.notify(record.exc_info, severity=severity)
        else:
            exc = Exception(record.message)
            bugsnag.notify(exc, severity=severity)