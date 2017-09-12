from __future__ import division, print_function, absolute_import

from celery.signals import task_failure
import bugsnag


def failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo,
                    **kw):
    task = {
        "task_id": task_id,
        "args": args,
        "kwargs": kwargs
    }

    bugsnag.auto_notify(exception, traceback=traceback,
                        context=sender.name,
                        extra_data=task,
                        unhandled=True,
                        severity_reason={
                            'type':'middleware_handler',
                            'attributes': {
                                'name': 'celery'
                            }
                        })


def connect_failure_handler():
    """
    Connect the bugsnag failure_handler to the Celery
    task_failure signal
    """
    task_failure.connect(failure_handler, weak=False)
