import logging
import bugsnag

class BugsnagHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

        # To enable support for django we try to run the django configure here, but 
        # fail gracefully if we couldnt import or it was not configured properly
        try:
          import bugsnag.django
          bugsnag.django.configure()
        except:
          pass

    def emit(self, record):
        if record.exc_info:
            bugsnag.notify(record.exc_info)
