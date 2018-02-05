# Bugsnag Chalice demo

This application demonstrates the usage of Bugsnag within a [Chalice application](https://github.com/aws/chalice).

Install dependencies

```shell
pip install -r requirements.txt
```

## Configuring Bugsnag and Chalice

There are two ways of setting up configuration for Bugsnag in your Chalice application:

1. Set the Bugsnag configuration up in ```app.py```:
    ```python
    bugsnag.configure(
        api_key = "YOUR_API_KEY",
        asynchronous = False,
        release_stage = "dev"
    )
    ```
    According to the [available configuration options](https://docs.bugsnag.com/platforms/python/other/configuration-options/)

1. To make your application more portable and pull configuration options from environment variables:
    ```python
    bugsnag.configure(
        api_key = os.environ.get('BUGSNAG_API_KEY'),
        asynchronous = False,
        release_stage = os.environ.get('BUGSNAG_RELEASE_STAGE')
    )
    ```
    This will allow you to set your API key and release stage as environment variables in your AWS lambda configuration, or in your ```.chalice/config.json``` file:
    ```json
    "environment_variables": {
        "BUGSNAG_API_KEY": "YOUR_API_KEY"
    },
    "stages": {
        "dev": {
        "api_gateway_stage": "api",
        "environment_variables": {
            "BUGSNAG_RELEASE_STAGE": "dev"
        }
        }
    }
    ```

In addition, ensure that a ```BugsnagHandler``` is registered with the applications logger, as this will allow Bugsnag to automatically be notified when an `error` log is made.
```python
handler = BugsnagHandler()
app.log.addHandler(handler)
```

## Running the example

To run the application locally, simply run:
```shell
chalice local
```

Check out the ```app.py``` file to see a list of available routes and how they are configured.