import bugsnag
import markdown
from django.http import HttpResponse


def index(request):
    with open('README.md') as fp:
        return HttpResponse(markdown.markdown(fp.read()))

def crash(request):
    raise Exception("Bugsnag Django demo says: It crashed! Go check " +
                    "bugsnag.com for a new notification!")

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
        "Bugsnag Django demo says: It crashed! But, due to the attached " +
        "callback the exception has meta information. Go check " +
        "bugsnag.com for a new notification (see the Diagnostics tab)!"
    )

def notify(request):
    msg = "Bugsnag Django demo says: False alarm, your application didn't crash"
    bugsnag.notify(Exception(msg));
    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check " +
        "<a href=\"bugsnag.com\">bugsnag.com</a> for a new notification.")

def notify_meta(request):
    bugsnag.notify(
        Exception("Bugsnag Django demo says: False alarm, your application didn't crash"),
        Diagnostics={ "code": 200, "message": "Django demo says: Everything is great" },
        User={ "email": "bugsnag@bugsnag.com", "username": "bob-hoskins" })
    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check " +
        " <a href=\"bugsnag.com\">bugsnag.com</a> for a new notification. " +
        "Check out the User tab for the meta data")

def context(request):
    bugsnag.notify(
        Exception("Bugsnag Django demo says: Changed the context to backgroundJob"),
        context="backgroundJob")
    return HttpResponse(
        "Bugsnag Django demo says: The context of the error is \"backgroundJob\" now")

def severity(request):
    bugsnag.notify(
        Exception("Bugsnag Django demo says: Look at the circle on the right side. It's different"),
        severity='info')
    return HttpResponse(
        "Bugsnag Django demo says: On <a href=\"bugsnag.com\">bugsnag.com</a> " +
        "look at the circle on the right side. It's different")
