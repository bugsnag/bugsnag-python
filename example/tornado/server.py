from tornado.ioloop import IOLoop
from tornado.web import Application, url
import bugsnag
import markdown
from bugsnag.tornado import BugsnagRequestHandler


class IndexHandler(BugsnagRequestHandler):
    def get(self):
        self.write(markdown.markdown(open('README.md').read()))


class CrashHandler(BugsnagRequestHandler):
    def get(self):
        raise Exception(
            "It crashed! Go check bugsnag.com for a new notification!"
        )


class CrashWithCallbackHandler(BugsnagRequestHandler):
    def get(self):
        bugsnag.before_notify(callback)
        raise Exception(
            "It crashed! But, due to the attached "
            + "callback the exception has meta information. Go check "
            + "bugsnag.com for a new notification (see the Diagnostics tab)!"
        )


def callback(notification):
    if notification.context == "GET /crash_with_callback":
        tab = {
            "message": "Everything is great",
            "code": 200,
        }
        notification.add_tab("Diagnostics", tab)


class NotifyHandler(BugsnagRequestHandler):
    def get(self):
        msg = "False alarm, your application didn't crash"
        bugsnag.notify(Exception(msg))
        self.write(
            "It didn't crash! But still go check "
            + "<a href=\"bugsnag.com\">bugsnag.com</a> for a new notification."
        )


class NotifyMetaHandler(BugsnagRequestHandler):
    def get(self):
        bugsnag.notify(
            Exception("False alarm, your application didn't crash"),
            Diagnostics={
                "code": 200,
                "message": "Tornado demo says: Everything is great",
            },
            User={"email": "bugsnag@bugsnag.com", "username": "bob-hoskins"},
        )
        self.write(
            "It didn't crash! But still go check "
            + "<a href=\"bugsnag.com\">bugsnag.com</a> for a new "
            + "notification. "
        )


class ContextHandler(BugsnagRequestHandler):
    def get(self):
        bugsnag.notify(
            Exception("Changed the context to backgroundJob"),
            context="backgroundJob",
        )
        self.write("The context of the error is \"backgroundJob\" now")


class SeverityHandler(BugsnagRequestHandler):
    def get(self):
        bugsnag.notify(
            Exception("Look at the circle on the right side. It's different"),
            severity='info',
        )
        self.write(
            "On <a href=\"bugsnag.com\">bugsnag.com</a> "
            + "look at the circle on the right side. It's different"
        )


bugsnag.configure(api_key="066f1ad3590596f9aacd601ea89af845",)


def make_app():
    return Application(
        [
            url(r"/", IndexHandler),
            url(r"/crash", CrashHandler),
            url(r"/crash_with_callback", CrashWithCallbackHandler),
            url(r"/notify", NotifyHandler),
            url(r"/notify_meta", NotifyMetaHandler),
            url(r"/context", ContextHandler),
            url(r"/severity", SeverityHandler),
        ],
        debug=True,
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8282)
    IOLoop.current().start()
