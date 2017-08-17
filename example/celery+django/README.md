# Bugsnag Django + Celery demo

This application demonstrates the usage of Bugsnag with the Django web framework for Python utilising the Celery module as a task runner.

Install dependencies

```shell
pip install -r requirements.txt
```

Django and Celery configuration files can be found in the ```celery_django``` folder.  

## Configuring Bugsnag and Django

1. Set the Django Bugsnag configuration up in ```settings.py```:
    ```python
    BUGSNAG = {
        'api_key': 'YOUR_API_KEY'
    }
    ```
    According to the [available configuration options](https://docs.bugsnag.com/platforms/python/django/configuration-options/)

2. Ensure the Bugsnag middleware is registered in ```settings.py``` at the top of the ```MIDDLEWARE_CLASSES```:
    ```python
    MIDDLEWARE_CLASSES = (
        "bugsnag.django.middleware.BugsnagMiddleware"
    )
    ```

For more information on setting up Bugsnag in Django please consult the [official documentation](https://docs.bugsnag.com/platforms/python/django/)

## Configuring Bugsnag and Celery

Configuration of celery in Django takes place in the ```celery.py``` file using the methods described in the [official documentation](https://docs.bugsnag.com/platforms/python/celery/)

1. Set the Celery Bugsnag configuration up in ```celery.py```:
    ```python
    import bugsnag
    bugsnag.configure(
        api_key = 'YOUR_API_KEY',
        ...
    )
    ```
    According to the [available configuration options](https://docs.bugsnag.com/platforms/python/django/configuration-options/)

2. Ensure the bugsnag failure handler has been added to celery:
    ```python
    from bugsnag.celery import connect_failure_handler
    connect_failure_handler()
    ```

In the case that the same configuration is to be used in both the Django and Celery instances, it is possible to import the bugsnag configuration from ```settings.py``` to use in ```celery.py```, ensuring configuration options need only be modified in a single location.

```python
from celery_django.settings import BUGSNAG as bugsnagconfig
import bugsnag
bugsnag.configure(**bugsnagconfig)
```

## Running the example

Once the app is configured it can be run using two terminal windows and the commands:
```shell
celery -A celery_django worker -l info
```
and
```shell
python manage.py runserver
```

After running the server head to the default path for more information on bugsnag logging examples