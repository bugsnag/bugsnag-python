import bugsnag
from django.http import HttpResponse


def callback(notification):
    """
    This callback will evaluate and modify every exception report, handled and
    unhandled, that occurs within the app, right before it is sent to Bugsnag.
    """
    # adding user info and metadata to every report:
    notification.user = {
        'name': 'Alan Turing',
        'email': 'turing@code.net',
        'password': 'password1',  # this will be filtered
        'id': '1234567890',
    }

    notification.add_tab('company', {'name': 'Stark Industries'})
    # checks every error, and adds special metadata only when the error class
    # is 'ValueError', as in crash_with_callback(), below.
    if isinstance(notification.exception, ValueError):
        tab = {"message": "That's not how this works", "code": 500}
        notification.add_tab("Diagnostics", tab)
        notification.context = (
            "Check the 'Diagnostics' tab attached only to ValueErrors"
        )


# attach the callback to your Bugsnag client.
bugsnag.before_notify(callback)


def index(request):
    """Homepage for this app.
    """
    with open('index.html') as fp:
        return HttpResponse(fp.read())


def crash(request):
    """Deliberately crashes with a raised exception.
    """
    raise Exception(
        "Bugsnag Django demo says: It crashed! Go check "
        + "bugsnag.com for a new notification!"
    )


def crash_with_callback(request):
    """
    Deliberately crashes with a ValueError, which the Bugsnag callback (above)
    will identify and attach special metadata to - *only* on this type of
    crash.
    """
    x = "string"
    y = int(x)
    print("x + y: ", x + y)


def handled(request):
    """
    Deliberately triggers a handled exception, and reports it to Bugsnag.
    """
    try:
        x = 1 / 0
        print("x: ", x)
    except ZeroDivisionError:
        bugsnag.notify(
            ZeroDivisionError('Django demo: To infinity... and beyond!')
        )

    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check "
        + "<a href=\"bugsnag.com\">bugsnag.com</a> for a new notification."
    )


def notify_meta(request):
    """
    Manually notifies Bugsnag of a handled exception, with some metadata
    locally attached.
    """
    bugsnag.notify(
        Exception('Django demo: Manual notification with metadata'),
        # this app adds some metadata globally, but you can also attach specfic
        # details to a particular exception.
        meta_data={
            'Request info': {'route': 'notifywithmetadata'},
            'Resolve info': {
                'status': 200,
                'message': 'Metadata has been added to this notification',
            },
        },
    )

    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check "
        + " <a href=\"bugsnag.com\">bugsnag.com</a> for a new notification. "
        + "Check out the User tab for the meta data"
    )


def context(request):
    """
    Sends a notification to Bugsnag which has a modified 'context', and a
    'severity' attribute that has been modifed to overwrite the default level
    (warning).
    """
    bugsnag.notify(
        Exception(
            'Django demo: Manual notification with context and severity'
        ),
        context='notifywithcontext',
        severity='info',
    )
    return HttpResponse(
        "Bugsnag Django demo says: It didn't crash! But still go check "
        + " <a href=\"bugsnag.com\">bugsnag.com</a> for a new notification. "
        + "The context and severity were changed."
    )
