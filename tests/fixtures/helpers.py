def invoke_exception_on_other_file(config):
    from bugsnag.event import Event

    return Event(Exception("another file!"), config, {})
