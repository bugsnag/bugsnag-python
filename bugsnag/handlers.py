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
        # Severity is not a one-to-one mapping, as there are only
        # a fixed number of severity levels available server side
        if record.levelname.lower() in ['error', 'critical']:
            severity = 'error'
        elif record.levelname.lower() in ['warning', ]:
            severity = 'warning'
        else:
            severity = 'info'

        # Only extract a few specific fields, as we don't want to
        # repeat data already being sent over the wire (such as exc)
        record_fields = ['asctime', 'created', 'levelname', 'levelno', 'msecs',
            'name', 'process', 'processName', 'relativeCreated', 'thread',
            'threadName', ]

        extra_data = dict([ ( field, getattr(record, field) ) 
            for field in record_fields ])

        if record.exc_info:
            bugsnag.notify(record.exc_info, severity=severity, extra_data=extra_data)
        else:
            # Create exception type dynamically, to prevent bugsnag.handlers
            # being prepended to the exception name due to class name
            # detection in utils. Because we are messing with the module
            # internals, we don't really want to expose this class anywhere
            level_name = record.levelname if record.levelname else "Message"
            exc_type = type('Log'+level_name, (Exception, ), {})
            exc = exc_type(record.message)
            exc.__module__ = '__main__'

            bugsnag.notify(exc, severity=severity, extra_data=extra_data)

