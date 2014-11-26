Bugsnag Notifier for Python
=========================

The Bugsnag Notifier for Python gives you instant notification of exceptions
thrown from your **Django**, **WSGI**, **Tornado**, **Flask** or **plain Python** app.
Any uncaught exceptions will trigger a notification to be sent to your
Bugsnag project.

[Bugsnag](http://bugsnag.com) captures errors in real-time from your web,
mobile and desktop applications, helping you to understand and resolve them
as fast as possible. [Create a free account](http://bugsnag.com) to start
capturing exceptions from your applications.


How to Install
--------------


### Django Apps

1.  Install the Bugsnag Notifier

    ```bash
    pip install bugsnag
    ```

1.  Configure the notifier in your Django `settings.py`:

    ```python
    BUGSNAG = {
        "api_key": "YOUR_API_KEY_HERE",
        "project_root": "/path/to/your/app",
    }
    ```

    If not set the project_root will default to the current working directory,
    and api_key will default to the `BUGSNAG_API_KEY` environment variable.

1.  Add the Bugsnag middleware to your app by editing your `MIDDLEWARE_CLASSES` in `settings.py`.

    ```python
    MIDDLEWARE_CLASSES = (
        ...
        "bugsnag.django.middleware.BugsnagMiddleware"
    )
    ```

### Flask Apps

1.  Install the Bugsnag Notifier

    ```bash
    pip install bugsnag
    ```

1.  Configure Bugsnag and attach it to Flask's exception handler

    ```python
    # Import bugsnag
    import bugsnag
    from bugsnag.flask import handle_exceptions

    # Configure Bugsnag
    bugsnag.configure(
      api_key = "YOUR_API_KEY_HERE",
      project_root = "/path/to/your/app",
    )

    # Attach Bugsnag to Flask's exception handler
    app = Flask(__name__)
    handle_exceptions(app)
    ```

### WSGI Apps

1.  Install the Bugsnag Notifier

    ```bash
    pip install bugsnag
    ```

1.  Configure Bugsnag and attach the WSGI middleware

    ```python
    # Configure Bugsnag
    import bugsnag
    from bugsnag.wsgi.middleware import BugsnagMiddleware

    bugsnag.configure(
      api_key = "YOUR_API_KEY_HERE",
      project_root = "/path/to/your/app",
    )

    # Wrap your WSGI app with Bugsnag
    application = BugsnagMiddleware(application)
    ```

### Tornado Apps

1.  Install the Bugsnag Notifier

    ```bash
    pip install bugsnag
    ```

1.  Configure the notifier when your python app starts

    ```python
    import bugsnag
    bugsnag.configure(
      api_key = "YOUR_API_KEY_HERE",
      project_root = "/path/to/your/app",
    )
    ```

2.  Have your request handlers inherit from `BugsnagRequestHandler`

    ```python
    from bugsnag.tornado import BugsnagRequestHandler

    class MyHandler(BugsnagRequestHandler):
        # ...
    ```

### Bottle Apps

1. Install the Bugsnag notifier

    ```bash
    pip install bugsnag
    ```

2. Configure the notifier when your python app starts

    ```python
    import bugsnag
    bugsnag.configure(
        api_key = "YOUR_API_KEY_HERE",
        project_root = "/path/to/your/app"
    )
    ```

3. Add the Bugsnag middleware

    ```python
    import bottle
    from bugsnag.wsgi.middleware import BugsnagMiddleware

    app = bottle.app()
    # Don't catch exceptions in bottle.
    app.catchall = False
    # Catch them in Bugsnag instead.
    myapp = BugsnagMiddleware(app)
    bottle.run(app=myapp)
    ```

### Celery

1. Install the Bugsnag notifier

    ```bash
    pip install bugsnag
    ```

1. Configure the notifier in your worker module

    ```python
    import bugsnag
    bugsnag.configure(
        api_key = "YOUR_API_KEY_HERE",
        project_root = "/path/to/your/app"
    )
    ```

1. Add the bugsnag failure handler to celery

    ```python
    from bugsnag.celery import connect_failure_handler
    connect_failure_handler()
    ```

### Other Python Apps

1.  Install the Bugsnag Notifier

    ```bash
    pip install bugsnag
    ```

1.  Configure the notifier when your python app starts

    ```python
    import bugsnag
    bugsnag.configure(
      api_key = "YOUR_API_KEY_HERE",
      project_root = "/path/to/your/app",
    )
    ```


Sending Handled Exceptions to Bugsnag
---------------------------------------

Unhandled exceptions are automatically sent to Bugsnag by the notifier.
If you would like to send handled exceptions to Bugsnag, you should import
the `bugsnag` module:

```python
import bugsnag
```

Then to notify Bugsnag of an error, you can call `bugsnag.notify`:

```python
bugsnag.notify(Exception("Something broke!"))
```

You can also pass [additional configuration setting](#per-request-configuration)
in as named parameters. These parameters will only affect the current call
to notify. For example:

```python
bugsnag.notify(Exception("Something broke!"),
    context="myContext",
    extra_data={"request_id": 12345, "message_id": 854},
)
```

### Using the logging framework

You can also hook Bugsnag up to Python's [logging
framework](https://docs.python.org/2/library/logging.html) so that anything of
level error or above is logged to Bugsnag.

Here is a plain Python example:

```python
import logging

from bugsnag.handlers import BugsnagHandler

#call bugsnag.configure() here
logger = logging.getLogger("test.logger")
logger.addHandler(BugsnagHandler())
```

*extra_fields*

The BugsnagHandler accepts a special keyword argument to its `__init__()`
function: 'extra_fields'.  This is optional and may be a dictionary of 
extra attributes to gather from each LogRecord and insert into meta_data
so they get sent to Bugsnag.  The keys in this dictionary should be tab
names for where you would like the data displayed in Bugsnag, like the 
top level keys in meta_data.  The values should be attributes to pull
off each log record and enter into that meta_data section.  The attributes 
do not need to exist on the log record, if they don't exist they will
just be ignored.  Example:

```python
bs_handler = BugsnagHandler(extra_fields={"some_tab":["context_attribute"]})
```

This is very useful if you are assigning context-specific attributes
to your LogRecord objects, as [described in the python logging cookbook](https://docs.python.org/3.4/howto/logging-cookbook.html#using-filters-to-impart-contextual-information).

###Logging Framework + Django
In django, you can use this configuration in your settings.py. For
other apps and frameworks, you can configure the handler as appropriate.

    ```python
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,

        'root': {
            'level': 'ERROR',
            'handlers': ['bugsnag'],
        },

        'handlers': {
            'bugsnag': {
                'level': 'INFO',
                'class': 'bugsnag.handlers.BugsnagHandler',
            },
        }
    }
    ```

Configuration
-------------

To configure additional Bugsnag settings, pass the settings as named parameters to the
`bugsnag.configure` method. For example:

```python
bugsnag.configure(
    api_key = "YOUR_API_KEY_HERE",
    use_ssl = True,
    notify_release_stages = ["production", "development"],
)
```

If you are using Django, you can instead add a dictionary called `BUGSNAG` to
your settings.py file. For example:

```python
BUGSNAG = {
    "api_key": "YOUR_API_KEY_HERE",
    "use_ssl": True,
    "notify_release_stages": ["production", "development"],
}
```

The available settings are detailed below.

###api_key

Your Bugsnag API key (required).

```python
bugsnag.configure(api_key = "YOUR_API_KEY_HERE")
```

###release_stage

If you would like to distinguish between errors that happen in different
stages of the application release process (development, production, etc)
you can set the `release_stage` that is reported to Bugsnag.

```python
bugsnag.configure(release_stage = "development")
```

In Django apps this value is automatically set to "development" if
the server running is the Django development server. Otherwise the default is
"production".

###notify_release_stages

By default, we will only notify Bugsnag of exceptions that happen when
your `release_stage` is set to be "production". If you would like to
change which release stages notify Bugsnag of exceptions you can
set `notify_release_stages`:

```python
bugsnag.configure(notify_release_stages = ["production", "development"])
```

###auto_notify

By default, we will automatically notify Bugsnag of any fatal exceptions
in your application. If you want to stop this from happening, you can set
`auto_notify`:

```python
bugsnag.configure(auto_notify = False)
```

###use_ssl

Enforces all communication with bugsnag.com be made via ssl.

```python
bugsnag.configure(use_ssl = True)
```

By default, `use_ssl` is set to false.

###project_root

We mark stacktrace lines as `inProject` if they come from files inside your
`project_root`.

```python
bugsnag.configure(project_root = "/var/www/myproject")
```

###app_version

If you want to track which versions of your application each exception
happens in, you can set `app_version`. This is set to `None` by default.

```python
bugsnag.configure(app_version = "2.5.1")
```

###params_filters

Sets the strings to filter out from the `params` hashes before sending
them to Bugsnag. Use this if you want to ensure you don't send
sensitive data such as passwords, and credit card numbers to our
servers. Any keys which contain these strings will be filtered.

```python
bugsnag.configure(params_filters = ["credit_card_number"])
```

By default, `params_filters` is set to `["password", "password_confirmation"]`

###ignore_classes

Sets which exception classes should never be sent to Bugnsag. This feature is
useful when you have a large number of 404 errors and dont want them all sent
to Bugsnag.

```python
bugsnag.configure(ignore_classes = ["django.http.Http404"])
```

By default, `ignore_classes` is set to `[]`

Per-request Configuration
-------------------------

The following configuration options can be set on a *per-request* basis.
Setting or overriding these allows you to attach useful request-specific
data along with exceptions, which can speed up debugging.

To configure these settings, you can call `bugsnag.configure_request`,
for example:

```python
bugsnag.configure_request(
    context = "/users",
    user = {"id":"bob-hoskins"},
)
```

The available settings are detailed below.

###context

A string representing what was happening in your application at the time of
the error. In Django apps, this is automatically set to be the path of the
current request.

```python
bugsnag.configure_request(context = "/users")
```

###user

A dictionary of "id", "email", and "name" that are used to identify and search for
the user in Bugsnag.

By default the "id" is set to the username of the current django user, or the IP
address of the connection.


```python
bugsnag.configure_request(user={"id":"bob-hoskins", "name": "Bob Hoskins", "email": "foo@bar.com"})
```

(The legacy parameter `user_id` acts as though you set a user hash with just the id property).

###meta_data

A dictionary of dictionaries, each of which appears as a tab on the Bugsnag dashboard.

```python
bugsnag.configure_request("metadata":{"account":{"name":"ACME Inc.", "premium": True}})
```

The deprecated parameters `session_data`, `environment_data`, `request_data`
and `extra_data` can be used to set the "session", "environment", "request" and
"extra" tabs of metadata if needed.

Notification options
--------------------

The `Bugsnag.notify` function accepts a large number of keyword arguments. These
can be used to override configuration or to send more data to bugsnag.

###traceback

The traceback to use for the exception. If omitted this will be read from `sys.exc_info`.

```python
bugsnag.notify(e, sys.exc_info()[2])
```

###api_key

Use a specific API key for this notification. (defaults to `bugsnag.configuration.api_key`)

```python
bugsnag.notify(e, api_key="YOUR_API_KEY_HERE")
```

###context

A string representing what was happening in your application at the time of
the error. In Django apps, this is automatically set to be the path of the
current request.

```python
bugsnag.notify(e, context="sign_up")
```

###severity

You can set the severity of an error in Bugsnag by including the severity option when
notifying bugsnag of the error,

```python
bugsnag.notify(Exception("Something broke!"), severity="error")
```

Valid severities are `error`, `warning` and `info`.

Severity is displayed in the dashboard and can be used to filter the error list.
By default all crashes (or unhandled exceptions) are set to `error` and all
`bugsnag.notify` calls default to `warning`.

###user

Information about the user currently using your app. This should be a dictionary
containing "id", "email" and "name" keys.

```python
bugsnag.notify(e, user={"id":"bob-hoskins", name: "Bob Hoskins", email: "foo@bar.com"})
```

###meta_data

A dictionary of dictionaries. Each dictionary will show up as a tab on Bugsnag.

```
bugsnag.notify(e, "metadata":{"account":{"name":"ACME Inc.", "premium": True}})
```

Any key that has no other meaning will also be treated as meta-data, so you could
have done:

```
bugsnag.notify(e, {"account":{"name":"ACME Inc.", "premium": True})
```

###grouping_hash

A string to use to group errors using your own custom grouping algorithm.

```python
bugsnag.notify(e, grouping_hash="/path/to/file.py:30|RuntimeError")
```

Before Notify Callbacks
-----------------------

If you need to modify the payload before sending it to bugsnag you can register a
before-notify callback:

```
def callback(notification):

    # if you return False, the notification will not be sent to
    # Bugsnag. (see ignore_classes for simple cases)
    if isinstance(notification.exception, KeyboardInterrupt):
        return False

    # You can set properties of the notification and
    # add your own custom meta-data.
    notification.user = {"id": current_user.id, "name": current_user.name, "email": current_user.email}
    notification.add_tab("account", {"paying": current_user.acccount.is_paying()}

bugsnag.before_notify(callback)
```

Reporting Bugs or Feature Requests
----------------------------------

Please report any bugs or feature requests on the github issues page for this
project here:

<https://github.com/bugsnag/bugsnag-python/issues>


Contributing
------------

-   [Fork](https://help.github.com/articles/fork-a-repo) the [notifier on github](https://github.com/bugsnag/bugsnag-python)
-   Commit and push until you are happy with your contribution
-   Install [nosetests](https://nose.readthedocs.org/) with `pip install nose`
-   Run the tests:

    ```bash
    ./setup.py test
    ```

-   [Make a pull request](https://help.github.com/articles/using-pull-requests)
-   Thanks!


License
-------

The Bugsnag python notifier is free software released under the MIT License.
See [LICENSE.txt](https://github.com/bugsnag/bugsnag-python/blob/master/LICENSE.txt) for details.
