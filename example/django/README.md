# Bugsnag Django demo

This Django application demonstrates how to use Bugsnag with the Django web
framework for Python. Before testing it, open up the `bugsnag_demo/settings.py`
file and configure your API key (see the very bottom of the file).

```
BUGSNAG = {
    "api_key": "066f1ad3590596f9aacd601ea89af845"
}
```

Install dependencies.

```
pip install -r requirements.txt
```

This minimal setup is enough to start Bugsnagging.

Run the application.

```
python manage.py runserver
```

Next, open your project's dashboard on Bugsnag.

1. [crash](/crash)
<br/>
Crashes the library and sends a notification about the nature of the crash.
Basically, almost any unhandled exception sends a notification to Bugsnag.
Pressing this link would lead to an empty page, which is normal.
See `demo/views.py, #crash`

1. [crash and use callbacks](/crash_with_callback)
<br/>
Before crashing, the library would append the Diagnostics tab with some
predefined information, attached by means of a callback.
Pressing this link would lead to an empty page, which is normal.
See `demo/views.py, #crash_with_callback`

1. [notify](/notify)
<br/>
Bugsnag Python provides a way to send notifications on demand by means of
`bugsnag.notify()`. This API allows to send notifications manually, without
crashing your code.  See `demo/views.py, #notify`


1. [notify with meta data](/notify_meta)
<br/>
Same as `notify`, but also attaches meta data. The meta data is any additional
information you want to attach to an exception. In this artificial case
additional information will be sent and displayed in a new tab called
Diagnostics.
See `demo/views.py, #notify_meta`

1. [context](/context)
<br/>
The context shows up prominently in the list view so that you can get an idea of
where a problem occurred. You can set it by providing the `context` option.
See `demo/views.py, #context`

1. [severity](/)
<br/>
You can set the severity of an error in Bugsnag by including the severity option
when notifying bugsnag of the error. Valid severities are `error`, `warning` and
`info`.
See `demo/views.py, #severity`
