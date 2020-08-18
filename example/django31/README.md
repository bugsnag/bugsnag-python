# Bugsnag Django demo

This Django application demonstrates how to use Bugsnag with the Django web framework for Python.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how breadcrumbs are left, how errors are grouped and how they relate to the original source.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!


1. Clone the repo and `cd` into this directory:

    ```shell
    git clone https://github.com/bugsnag/bugsnag-python.git
    cd bugsnag-python/example/django31
    ```

1. Install dependencies

    ```shell
    pip install -r requirements.txt
    ```

1. Run the application

    ```shell
    BUGSNAG_API_KEY='your api key here!' python manage.py runserver
    ```

1. View the example page which will, by default, be served at: http://localhost:8000

For more information, see [our Django documentation](https://docs.bugsnag.com/platforms/python/django/).
