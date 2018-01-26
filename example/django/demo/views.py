import bugsnag
import markdown
from django.http import HttpResponse

# *******************************************************
def callback(notification):
    """This callback will evaluate and modify every exception report, handled and unhandled, that occurs within the app, right before it is sent to Bugsnag.
    """
    # adding user info and metadata to every report:
    notification.user = {
        # in your app, you can pull these details from session.
        'name': 'Alan Turing',
        'email': 'turing@code.net',
        'id': '1234567890'
    }

    notification.add_tab(
        'company', {
            'name': 'Stark Industries'
        }
    )

    if notification.context == "demo.views.crash_with_callback":
        tab = {
            "message": "Django demo says: Everything is great",
            "code": 200
        }
        notification.add_tab("Diagnostics", tab)

bugsnag.before_notify(callback)
# *****************************************************



def index(request):
    with open('index.html') as fp:
        return HttpResponse(fp.read())


def crash(request):
    raise Exception("Bugsnag Django demo says: It crashed! Go check " +
                    "bugsnag.com for a new notification!")


def crash_with_callback(request):

    raise Exception(
        "Bugsnag Django demo says: It crashed! But, due to the attached " +
        "callback the exception has meta information. Go check " +
        "bugsnag.com for a new notification (see the Diagnostics tab)!"
    )


def notify(request):
    msg = "Bugsnag Django demo says: False alarm, your application didn't crash"
    bugsnag.notify(Exception(msg))
    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check " +
        "<a href=\"bugsnag.com\">bugsnag.com</a> for a new notification.")


def notify_meta(request):
    """Manually notifies Bugsnag of a handled exception, with some metadata locally attached.
    """
    bugsnag.notify(
        Exception('Django demo: Manual notification with metadata'),
        # this app adds some metadata globally, but you can also attach specfic details to a particular exception
        meta_data = {
            'Request info': {
                'route': 'notifywithmetadata',
                'headers': request.headers
            },
            'Resolve info': {
                'status': 200,
                'message': 'Metadata has been added to this notification'
            }
        },
    )

    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check " +
        " <a href=\"bugsnag.com\">bugsnag.com</a> for a new notification. " +
        "Check out the User tab for the meta data")


def context(request):
    """Notifies Bugsnag of a handled exception, which has a modified 'context' attribute for the purpose of improving how these exceptions will group together in the Bugsnag dashboard, and a severity attribute that has been modifed to overwrite the default level (warning).
    """
    bugsnag.notify(
        Exception('Flask demo: Manual notification with context and severity'),
        context = 'notifywithcontext',
        severity = 'info'
    )
    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check " +
        " <a href=\"bugsnag.com\">bugsnag.com</a> for a new notification. " +
        "The context and severity were changed.")
