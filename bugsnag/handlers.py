import logging
import bugsnag
import bugsnag.django

class BugsnagHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

        bugsnag.django.configure()

    def emit(self, record):
        if record.exc_info:
            bugsnag.notify(record.exc_info)
