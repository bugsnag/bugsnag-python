# Bugsnag Django demo

This Django application demonstrates how to use Bugsnag with the Django web framework for Python.

Please note this particular example app will only work with Python 3+ and Django 2+, to showcase the most current configurations. Check out [this example](https://github.com/bugsnag/bugsnag-python/example/django1.11) to see the configuration for  Python 2 and Django 1.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how breadcrumbs are left, how errors are grouped and how they relate to the original source.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!


1. Clone the repo and `cd` into this directory:
    ```shell
    git clone https://github.com:bugsnag/bugsnag-python.git
    cd bugsnag-python/example/django
    ```

1. Install dependencies
    ```shell
    pip install -r requirements.txt
    ```

1. Before testing it, open up the [`settings.py`](bugsnag_demo/settings.py)
    file and configure your API key.

1. Confirm that Bugsnag middleware is added to the top of MIDDLEWARE in [`settings.py`](bugsnag_demo/settings.py)
    ```shell
    MIDDLEWARE = (
    'bugsnag.django.middleware.BugsnagMiddleware',
    ...
    )
    ```

1. Run the application. (Make sure to use any 3+ version of python.)
    ```shell
    python manage.py runserver
    ```

1. View the example page which will (most likely) be served at: http://localhost:8000

For more information, see our documentation:
https://docs.bugsnag.com/platforms/python/django/
