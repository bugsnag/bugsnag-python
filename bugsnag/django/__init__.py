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


def add_django_request_to_notification(event):
    if not hasattr(event.request_config, "django_request"):
        return

    request = event.request_config.django_request
    event.request = request

    if event.context is None:
        try:
            route = resolve(request.path_info)
        except Resolver404:
            route = None

        if route and route.url_name:
            event.context = route.url_name
        elif route and route.view_name:
            event.context = route.view_name
        else:
            event.context = "%s %s" % (request.method, request.path_info)

    if hasattr(request, 'user'):
        if callable(request.user.is_authenticated):
            is_authenticated = request.user.is_authenticated()
        else:
            is_authenticated = request.user.is_authenticated
        if is_authenticated:
            try:
                name = request.user.get_full_name()
                email = getattr(request.user, 'email', None)
                username = str(request.user.get_username())
                event.set_user(id=username, email=email, name=name)
            except Exception:
                event.config.logger.exception('Could not get user data')
    else:
        event.set_user(id=request.META['REMOTE_ADDR'])

    if getattr(request, "session", None):
        event.add_tab("session", dict(request.session))
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

    event.add_tab("request", request_tab)
    if bugsnag.configure().send_environment:
        event.add_tab("environment", dict(request.META))


def configure():
    config = bugsnag.configure()

    # default to development if in DEBUG mode
    if getattr(settings, 'DEBUG'):
        config.configure(release_stage='development')

    # Import Bugsnag settings from settings.py
    django_bugsnag_settings = getattr(settings, 'BUGSNAG', {})
    config.configure(**django_bugsnag_settings)

    middleware = config.internal_middleware
    middleware.before_notify(add_django_request_to_notification)

    config.runtime_versions['django'] = django.__version__

    request_started.connect(__track_session)
    got_request_exception.connect(
        __handle_request_exception(config.logger),
        weak=False
    )

    return config


def __track_session(sender, **extra):
    if bugsnag.configuration.auto_capture_sessions:
        bugsnag.start_session()


def __handle_request_exception(logger):
    def inner(sender, **kwargs):
        request = kwargs.get('request', None)

        if request is not None:
            bugsnag.configure_request(django_request=request)

        try:
            bugsnag.auto_notify_exc_info(severity_reason={
                "type": "unhandledExceptionMiddleware",
                "attributes": {"framework": "Django"}
            })
        except Exception:
            logger.exception("Error in exception middleware")

    return inner
