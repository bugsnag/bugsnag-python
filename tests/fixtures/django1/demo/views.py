import bugsnag
import markdown
from django.http import HttpResponse


def index(request):
    with open('README.md') as fp:
        return HttpResponse(markdown.markdown(fp.read()))


def crash(request):
    raise Exception("crash!")


def callback(notification):
    if notification.context == "demo.views.crash_with_callback":
        tab = {
            "message": "Django demo says: Everything is great",
            "code": 200
        }
        notification.add_tab("Diagnostics", tab)


def crash_with_callback(request):
    bugsnag.before_notify(callback)
    raise Exception(
        "crash with callback!"
    )


def notify(request):
    msg = "notify!"
    bugsnag.notify(Exception(msg))
    return HttpResponse("notify!")


def notify_meta(request):
    bugsnag.notify(
        Exception("notify meta!"),
        Diagnostics={
            "code": 200,
            "message": "Django demo says: Everything is great"
        },
        User={"email": "bugsnag@bugsnag.com", "username": "bob-hoskins"})
    return HttpResponse("notify meta!")


def context(request):
    bugsnag.notify(
        Exception("context!"),
        context="backgroundJob")
    return HttpResponse("context!")


def severity(request):
    bugsnag.notify(
        Exception("severity!"),
        severity='info')
    return HttpResponse("severity!")
