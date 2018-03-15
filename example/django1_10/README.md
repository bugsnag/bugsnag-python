# Bugsnag Django 1.10+ demo

This Django application demonstrates how to use Bugsnag with the Django 1.10 web framework for Python 2+.

Please note that while our bugsnag-python notifier is compatible with more recent versions of Django and Python, this specific example app demonstrates how to configure Bugsnag with Django 1.10 (and subsequent versions prior to 2.0) and Python 2+ (prior to 3.0).  We have a separate example for Django 2+ with Python 3+, which can be viewed [here](https://github.com/bugsnag/bugsnag-python/example/django).

We also support versions of Django prior to 1.10, with some configuration changes. See [our documentation](https://docs.bugsnag.com/platforms/python/django/#basic-configuration) for further details.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how breadcrumbs are left, how errors are grouped and how they relate to the original source.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!


1. Clone the repo and `cd` into this directory:
    ```sh
    git clone https://github.com/bugsnag/bugsnag-python.git
    cd bugsnag-python/example/django1_10
    ```

1. Install dependencies
    ```shell
    pip install -r requirements.txt
    ```

1. Before testing it, open up the `settings.py`
    file and configure your API key.

1. Confirm that Bugsnag middleware is added to the top of MIDDLEWARE in [`settings.py`](bugsnag_demo/settings.py)
    ```shell
    MIDDLEWARE = (
    'bugsnag.django.middleware.BugsnagMiddleware',
    ...
    )
    ```

1. Run the application.
    ```shell
    python manage.py runserver
    ```

1. View the example page which will (most likely) be served at: http://localhost:8000

For more information, see our documentation:
https://docs.bugsnag.com/platforms/python/django/
