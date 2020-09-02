import celery
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
                        asynchronous=False,
                        severity_reason={
                            'type': 'unhandledExceptionMiddleware',
                            'attributes': {
                                'framework': 'Celery'
                            }
                        })


def connect_failure_handler():
    """
    Connect the bugsnag failure_handler to the Celery
    task_failure signal
    """
    bugsnag.configure().runtime_versions['celery'] = celery.__version__
    task_failure.connect(failure_handler, weak=False)
