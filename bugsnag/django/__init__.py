import six
import django
from django.conf import settings
from django.core.signals import request_started, got_request_exception

try:
    from django.core.urlresolvers import resolve, Resolver404
except ImportError:
    from django.urls import resolve, Resolver404

import bugsnag
from bugsnag.utils import is_json_content_type
import json


def add_django_request_to_notification(notification):
    if not hasattr(notification.request_config, "django_request"):
        return

    request = notification.request_config.django_request

    if notification.context is None:
        try:
            route = resolve(request.path_info)
        except Resolver404:
            route = None

        if route and route.url_name:
            notification.context = route.url_name
        elif route and route.view_name:
            notification.context = route.view_name
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
    request_tab = {
        'method': request.method,
        'path': request.path,
        'encoding': request.encoding,
        'GET': dict(request.GET),
        'POST': dict(request.POST),
        'url': request.build_absolute_uri(),
    }
    try:
        is_json = is_json_content_type(request.META.get('CONTENT_TYPE', ''))
        if is_json and request_tab["method"] == "POST":
            body = request.body.decode('utf-8', 'replace')
            request_tab["POST"] = json.loads(body)
    except Exception:
        pass

    notification.add_tab("request", request_tab)
    if bugsnag.configure().send_environment:
        notification.add_tab("environment", dict(request.META))


def configure():
    # default to development if in DEBUG mode
    if getattr(settings, 'DEBUG'):
        bugsnag.configure(release_stage='development')

    request_started.connect(__track_session)
    got_request_exception.connect(__handle_request_exception)

    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    bugsnag.configure(**django_bugsnag_settings)

    middleware = bugsnag.configure().internal_middleware
    middleware.before_notify(add_django_request_to_notification)

    bugsnag.configure().runtime_versions['django'] = django.__version__


def __track_session(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()


def __handle_request_exception(sender, **kwargs):
    request = kwargs.get('request', None)
    if request is not None:
        bugsnag.configure_request(django_request=request)
    try:
        bugsnag.auto_notify_exc_info(severity_reason={
            "type": "unhandledExceptionMiddleware",
            "attributes": {"framework": "Django"}
        })
    except Exception:
        bugsnag.logger.exception("Error in exception middleware")
