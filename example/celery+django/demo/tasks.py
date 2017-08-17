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
        bugsnag.notify(ZeroDivisionError('Celery+Django App: Caught and notified'))

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

@shared_task
def metadivide(x, y):
    try:
        return x/y
    except ZeroDivisionError as e:
        bugsnag.notify(ZeroDivisionError('Celery+Django App: ' +
            'View Diagnostics tab for more info'),
            meta_data = {
                'Diagnostics': {
                    'x': x,
                    'y': y
                }
            }
        )

@shared_task
def contextdivide(x, y):
    try:
        return x/y
    except ZeroDivisionError as e:
        bugsnag.notify(ZeroDivisionError('Celery+Django App: ' +
            'Check the context of the notification'),
            context = 'celery.tasks.contextdivide'
        )

@shared_task
def severitydivide(x, y):
    try:
        return x/y
    except ZeroDivisionError as e:
        bugsnag.notify(ZeroDivisionError('Celery+Django App: ' +
            'The severity symbol on the right has changed'),
            severity = 'info'
        )