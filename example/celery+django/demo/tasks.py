from __future__ import absolute_import, unicode_literals
from celery import shared_task
import bugsnag

@shared_task
def divide(x, y):
    return x/y

@shared_task
def safedivide(x, y):
    if y != 0:
        return x/y
    else:
        bugsnag.notify(ZeroDivisionError("Someone tried to divide by zero again"))

@shared_task
def reporteddivide(x, y):
    def callback(notification):
        if notification.context == 'demo.tasks.reporteddivide':
            notification.add_tab('Arguments', {
                'x': x,
                'y': y
            })
    bugsnag.before_notify(callback)
    return x/y
