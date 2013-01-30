import logging
import bugsnag

class BugsnagHandler(logging.Handler):
    def emit(self, record):
        print record.__dict__.keys()
        if record.exc_info:
            bugsnag.notify(record.exc_info)