import bugsnag

def configure():
    from django.conf import settings
    
    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)

    # Ignore django 404s by default
    bugsnag.configuration.ignore_classes.append("django.http.Http404")