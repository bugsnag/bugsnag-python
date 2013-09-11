from django.conf import settings

import bugsnag

def configure():
    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)

    # Ignore django 404s by default
    bugsnag.configuration.ignore_classes.append("django.http.Http404")