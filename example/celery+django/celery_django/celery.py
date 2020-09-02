import os
from celery import Celery
import bugsnag
from bugsnag.celery import connect_failure_handler
from celery_django.settings import BUGSNAG as bugsnagconfig

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_django.settings')

app = Celery('celery_django', broker='redis://localhost', backend='redis')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

bugsnag.configure(**bugsnagconfig)

connect_failure_handler()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
