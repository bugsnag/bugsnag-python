from celery.signals import task_failure

import bugsnag

def process_failure_signal(sender, task_id, exception, args, kwargs, traceback, einfo, **kw):
    task = {
        "task_id": task_id,
        "args": args,
        "kwargs": kwargs
    }

    bugsnag.notify(exception, traceback=traceback,
                              context=sender.name,
                              extra_data=task)

task_failure.connect(process_failure_signal, weak=False)
