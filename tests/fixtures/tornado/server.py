from tornado.ioloop import IOLoop
from tornado.web import Application, url
import bugsnag
from bugsnag.tornado import BugsnagRequestHandler


class CrashHandler(BugsnagRequestHandler):
    def get(self):
        raise Exception("Bugsnag Tornado demo says: It crashed! Go check " +
                        "bugsnag.com for a new notification!")

    def post(self):
        raise Exception("Bugsnag Tornado demo says: It crashed! Go check " +
                        "bugsnag.com for a new notification!")


class CrashWithCallbackHandler(BugsnagRequestHandler):
    def get(self):
        bugsnag.before_notify(callback)
        raise Exception(
            "Bugsnag Tornado demo says: It crashed! But, due to the " +
            "attached callback the exception has meta information. Go " +
            "check bugsnag.com for a new notification (see the " +
            "Diagnostics tab)!"
        )


def callback(notification):
    if notification.context == "GET /crash_with_callback":
        tab = {
            "message": "Tornado demo says: Everything is great",
            "code": 200
        }
        notification.add_tab("Diagnostics", tab)
    args = notification.request.query_arguments
    if 'user_id' in args:
        notification.set_user(id=args['user_id'][0])


class NotifyHandler(BugsnagRequestHandler):
    def get(self):
        msg = "Bugsnag Tornado demo says: False alarm, your application "
        msg += "didn't crash"
        bugsnag.notify(Exception(msg))
        self.write(
            "Bugsnag Tornado demo says: It didn't crash! But still go  " +
            "check <a href=\"bugsnag.com\">bugsnag.com</a> for a new " +
            "notification.")

    def post(self):
        msg = "Bugsnag Tornado demo says: False alarm, your application "
        msg += "didn't crash"
        bugsnag.notify(Exception(msg))
        self.write(
            "Bugsnag Tornado demo says: It didn't crash! But still go check " +
            "<a href=\"bugsnag.com\">bugsnag.com</a> for a new notification.")


bugsnag.configure(
    api_key="066f1ad3590596f9aacd601ea89af845",
    asynchronous=False
)


def make_app():
    return Application([
        url(r"/crash", CrashHandler),
        url(r"/crash_with_callback", CrashWithCallbackHandler),
        url(r"/notify", NotifyHandler),
        ], debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(8282)
    IOLoop.current().start()
