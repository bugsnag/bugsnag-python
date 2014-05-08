from __future__ import division, print_function, absolute_import

from django.conf import settings

import bugsnag

def add_django_request_to_notification(notification):
    if not hasattr(notification.request_config, "django_request"):
        return

    request = notification.request_config.django_request

    notification.context = request.path
    notification.set_user(id=request.META['REMOTE_ADDR'])
    notification.add_tab("session", dict(request.session))
    notification.add_tab("request", {
        'path': request.path,
        'encoding': request.encoding,
        'params': dict(request.REQUEST),
        'url': request.build_absolute_uri(),
    })
    notification.add_tab("environment", dict(request.META))

def configure():
    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)

    # Ignore django 404s by default
    bugsnag.configuration.ignore_classes.append("django.http.Http404")
    bugsnag.before_notify(add_django_request_to_notification)
