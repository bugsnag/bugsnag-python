# Bugsnag Django demo

This Django application demonstrates how to use Bugsnag with the Django web framework for Python.

Please note that while bugsnag-python is compatible with previous Python 2 and Django 1 versions -- however, this particular example app will only work with Python 3+ and Django 2+, to showcase the most current configurations. See [our documentation](https://docs.bugsnag.com/platforms/python/django/) for further details.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how breadcrumbs are left, how errors are grouped and how they relate to the original source.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!


1. Clone the repo and `cd` into this directory:
    ```sh
    git clone git@github.com:bugsnag/bugsnag-python.git
    cd bugsnag-python/example/django
    ```

1. Install dependencies
    ```shell
    pip3 install -r requirements.txt
    ```

1. Before testing it, open up the `settings.py`
    file and configure your API key.

1. Run the application. (Make sure to use any 3+ version of python.)
    ```shell
    python3.6 manage.py runserver
    ```

1. View the example page which will (most likely) be served at: http://localhost:8000

For more information, see our documentation:
https://docs.bugsnag.com/platforms/python/django/
