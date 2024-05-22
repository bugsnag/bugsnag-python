import os
import bugsnag
from celery import Celery
from bugsnag.celery import connect_failure_handler


bugsnag.configure(
    api_key=os.environ["BUGSNAG_API_KEY"],
    endpoint=os.environ["BUGSNAG_ERROR_ENDPOINT"],
    session_endpoint=os.environ["BUGSNAG_SESSION_ENDPOINT"],
)

app = Celery(
    'bugsnag_celery_test_app',
    broker='redis://redis:6379',
    backend='rpc://',
    include=['bugsnag_celery_test_app.tasks'],
)

connect_failure_handler()


if __name__ == '__main__':
    app.start()
