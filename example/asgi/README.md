# Bugsnag ASGI demo

This [Uvicorn](https://www.uvicorn.org/) app demonstrates how to use Bugsnag with ASGI.

## Setup

Try this out with [your own Bugsnag account](https://app.bugsnag.com/user/new)! You'll be able to see how the errors are reported in the dashboard, how breadcrumbs are left, how errors are grouped and how they relate to the original source.

To get set up, follow the instructions below. Don't forget to replace the placeholder API token with your own!

1.  Clone the repo and `cd` into this directory:
    ```
    git clone https://github.com/bugsnag/bugsnag-python.git
    cd bugsnag-python/example/asgi
    ```

2.  Install dependencies
    ```
    pip install -r requirements.txt
    ```

3.  Open `example.py` and configure your own API key
4.  Run the application:
    ```
    uvicorn example:app
    ```
5.  View the example page which will be served at: http://localhost:8000

For more information, see our documentation:
https://docs.bugsnag.com/platforms/python/asgi/
