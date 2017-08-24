# Bugsnag Django+Celery demo

This application demonstrates the use of Bugsnag with the Django web framework featuring Celery as a task-runner.

1. [Crash](/celerycrash)
<br/>
Creates a new task for Celery to run which will crash, generating a report in the Bugsnag dashboard.  Note that the response will not be an error report as the Celery process contains the error, not Django

2. [Crash and use callbacks](/celerycallback)
<br/>
Before crashing, the library would append the Diagnostics tab with some
predefined information, attached by means of a callback.

3. [Notify](/celerynotify)
<br/>
Bugsnag Python provides a way to send notifications on demand by means of
`bugsnag.notify()`. This API allows to send notifications manually, without
crashing your code.

4. [Notify with meta data](/celerynotifymetadata)
<br/>
Same as `notify`, but also attaches meta data. The meta data is any additional
information you want to attach to an exception. In this artificial case
additional information will be sent and displayed in a new "Diagnostics tabs"

5. [Notify with context](/celerynotifycontext)
<br/>
The context shows up prominently in the list view so that you can get an idea of
where a problem occurred. You can set it by providing the `context` option.

6. [Notify with severity](/celerynotifyseverity)
<br/>
You can set the severity of an error in Bugsnag by including the severity option
when notifying Bugsnag of the error. Valid severities are `error`, `warning` and
`info`.