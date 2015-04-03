"""
This example shows how to send exceptions in celery tasks to Bugsnag.

First:

    Change the API key below to your API key,

Then, in one terminal, run:

    celery -A example.tasks

And, in another, run:

    python -m example.tasks

You will see a zero-division error appear in Bugsnag.
"""

from celery import Celery
import bugsnag
from bugsnag.celery import connect_failure_handler

celery = Celery('tasks', broker='redis://localhost', backend='redis')

bugsnag.configure(api_key="066f5ad3590596f9aa8d601ea89af845")
connect_failure_handler()

@celery.task(name='tasks.divide')
def divide(x, y):
    return x / y

if __name__ == "__main__":
    divide.delay(1, 0)
