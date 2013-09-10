import logging
import bugsnag


class BugsnagHandler(logging.Handler):
    def emit(self, record):
        if record.msg:
            if isinstance(record.msg, basestring):
                bugsnag.notify(Exception(record.msg))
            else:
                bugsnag.notify(record.msg)
