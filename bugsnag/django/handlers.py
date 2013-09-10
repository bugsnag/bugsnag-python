from django.conf import settings

import logging
import bugsnag


class BugsnagHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        # Ignore django 404s by default
        bugsnag.configuration.ignore_classes.append("django.http.Http404")

        # Import Bugsnag settings from settings.py
        django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
        bugsnag.configure(**django_bugsnag_settings)
    
    def emit(self, record):
        print record.__dict__.keys()
        if record.exc_info:
            bugsnag.notify(record.exc_info)
