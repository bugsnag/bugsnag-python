from __future__ import division, print_function, absolute_import

import six
from django.conf import settings
from django.core.signals import request_started

try:
    from django.core.urlresolvers import resolve
except ImportError:
    from django.urls import resolve

import bugsnag


def add_django_request_to_notification(notification):
    if not hasattr(notification.request_config, "django_request"):
        return

    request = notification.request_config.django_request

    if notification.context is None:
        route = resolve(request.path_info)
        if route:
            notification.context = route.url_name
        else:
            notification.context = "%s %s" % (request.method,
                                              request.path_info)

    if hasattr(request, 'user'):
        if callable(request.user.is_authenticated):
            is_authenticated = request.user.is_authenticated()
        else:
            is_authenticated = request.user.is_authenticated
        if is_authenticated:
            try:
                name = request.user.get_full_name()
                email = getattr(request.user, 'email', None)
                username = six.text_type(request.user.get_username())
                notification.set_user(id=username, email=email, name=name)
            except Exception:
                bugsnag.logger.exception('Could not get user data')
    else:
        notification.set_user(id=request.META['REMOTE_ADDR'])

    if getattr(request, "session", None):
        notification.add_tab("session", dict(request.session))
    notification.add_tab("request", {
        'method': request.method,
        'path': request.path,
        'encoding': request.encoding,
        'GET': dict(request.GET),
        'POST': dict(request.POST),
        'url': request.build_absolute_uri(),
    })
    notification.add_tab("environment", dict(request.META))


def configure():
    # default to development if in DEBUG mode
    if getattr(settings, 'DEBUG'):
        bugsnag.configure(release_stage='development')

    request_started.connect(__track_session)

    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)

    bugsnag.before_notify(add_django_request_to_notification)


def __track_session(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()
