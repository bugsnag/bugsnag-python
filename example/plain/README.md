# Bugsnag Python demo

This application demonstrates the usage of Bugsnag with Python.

Install dependencies

```shell
pip install -r requirements.txt
```

## Configuring Bugsnag

Set the Bugsnag configuration up in ```app.py```:
```python
bugsnag.configure(
    api_key='YOUR_API_KEY'
)
```
According to the [available configuration options](https://docs.bugsnag.com/platforms/python/other/configuration-options/)

For more information on setting up Bugsnag in Python please consult the [official documentation](https://docs.bugsnag.com/platforms/python/other)

## Running the example

Once the app is configured it can be run using the command:
```shell
python app.py
```

After running the example head to the [Bugsnag dashboard](https://app.bugsnag.com) to see the generated notifications.