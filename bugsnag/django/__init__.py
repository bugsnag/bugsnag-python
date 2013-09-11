from django.conf import settings

import bugsnag

def configure():
    # Ignore django 404s by default
    print "Configuring!"
    bugsnag.configuration.ignore_classes.append("django.http.Http404")

    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)
    print bugsnag.configuration.api_key