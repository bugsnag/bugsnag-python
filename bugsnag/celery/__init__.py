from celery.signals import task_failure

import bugsnag

def process_failure_signal(sender, task_id, exception, args, kwargs, traceback, einfo, **kw):
    if hasattr(einfo, 'exc_info'):
        # for Celery 2.4 or later
        exc_info = einfo.exc_info
    else:
        # for Celery before 2.4
        exc_info = (type(exception), exception, traceback)

    # Send the exception to bugsnag
    bugsnag.notify(exception, context="celery", extra_data={"task_id": task_id})

task_failure.connect(process_failure_signal, weak=False)