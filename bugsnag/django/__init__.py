from __future__ import division, print_function, absolute_import

from django.conf import settings
from django.core.urlresolvers import resolve

import bugsnag

def add_django_request_to_notification(notification):
    if not hasattr(notification.request_config, "django_request"):
        return

    request = notification.request_config.django_request

    notification.context = request.path

    if hasattr(request, 'user') and request.user.is_authenticated():
        try:
            name = " ".join([request.user.first_name or '', request.user.last_name or ''])
            notification.set_user(id=request.user.username, email=request.user.email, name=name)
        except Exception as e:
            bugsnag.warn("could not get user data: %s" % e)

    else:
        notification.set_user(id=request.META['REMOTE_ADDR'])

    route = resolve(request.path_info)
    if route:
        notification.context = route.url_name
    else:
        notification.context = "%s %s" % (request.method, request.path_info)

    notification.add_tab("session", dict(request.session))
    notification.add_tab("request", {
        'path': request.path,
        'encoding': request.encoding,
        'params': dict(request.REQUEST),
        'url': request.build_absolute_uri(),
    })
    notification.add_tab("environment", dict(request.META))

def configure():
    # default to development if in DEBUG mode
    if getattr(settings, 'DEBUG'):
        bugsnag.configure(release_stage='development')

    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)

    bugsnag.before_notify(add_django_request_to_notification)
