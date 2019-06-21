# Bugsnag Bottle demo

This Bottle application demonstrates how to use Bugsnag with the Bottle web framework for Python.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how breadcrumbs are left, how errors are grouped and how they relate to the original source.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!

1. Clone the repo and `cd` into this directory:
    ```shell
    git clone https://github.com/bugsnag/bugsnag-python.git
    cd bugsnag-python/example/bottle
    ```

1. Install dependencies
    ```shell
    pip install -r requirements.txt
    ```

1. Before testing it, open up the `server.py`
file and configure your API key.

1. Run the application.
    ```shell
    python server.py
    ```

1. View the example page which will be served at: http://localhost:8080

For more information, see our documentation:
https://docs.bugsnag.com/platforms/python/bottle/
