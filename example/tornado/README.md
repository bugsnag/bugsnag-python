# Bugsnag Tornado demo

This Tornado application demonstrates how to use Bugsnag with the Tornado web
framework for Python. Before testing it, open up the `server.py`
file and configure your API key.

```
BUGSNAG = {
    "api_key": "066f1ad3590596f9aacd601ea89af845"
}
```

Run the application.

```
python server.py
```

Next, open your project's dashboard on Bugsnag.

1. [crash](/crash)
<br/>
Crashes the library and sends a notification about the nature of the crash.
Basically, almost any unhandled exception sends a notification to Bugsnag.
Pressing this link would lead to an empty page, which is normal.
See `server.py, CrashHandler`

1. [crash and use callbacks](/crash_with_callback)
<br/>
Before crashing, the library would append the Diagnostics tab with some
predefined information, attached by means of a callback.
Pressing this link would lead to an empty page, which is normal.
See `server.py, CrashWithCallbackHandler`

1. [notify](/notify)
<br/>
Bugsnag Python provides a way to send notifications on demand by means of
`bugsnag.notify()`. This API allows to send notifications manually, without
crashing your code.
See `server.py, NotifyHandler`

1. [notify with meta data](/notify_meta)
<br/>
Same as `notify`, but also attaches meta data. The meta data is any additional
information you want to attach to an exception. In this artificial case
additional information will be sent and displayed in a new tab called
Diagnostics.
See `server.py, NotifyMetaHandler`

1. [context](/context)
<br/>
The context shows up prominently in the list view so that you can get an idea of
where a problem occurred. You can set it by providing the `context` option.
See `server.py, ContextHandler`

1. [severity](/)
<br/>
You can set the severity of an error in Bugsnag by including the severity option
when notifying Bugsnag of the error. Valid severities are `error`, `warning` and
`info`.
See `server.py, SeverityHandler`
