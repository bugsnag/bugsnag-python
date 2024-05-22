import bugsnag
from celery import shared_task
from bugsnag_celery_test_app.main import app


@app.task
def handled():
    bugsnag.notify(Exception('oooh nooo'))

    return 'hello world'


@app.task
def unhandled():
    a = {}

    return a['b']


@app.task
def add(*args, a, b):
    total = int(a) + int(b)

    for arg in args:
        total += int(arg)

    assert total < 100

    return total


@shared_task
def divide(a, b):
    return int(a) / int(b)
