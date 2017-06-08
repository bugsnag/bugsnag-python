def invoke_exception_on_other_file(config):
    from bugsnag.notification import Notification

    return Notification(Exception("another file!"), config, {})
