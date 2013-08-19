Bugsnag Notifier for Python
=========================

The Bugsnag Notifier for Python gives you instant notification of exceptions
thrown from your **Django** or **plain Python** app.
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
    
1.  Add Bugsnag to the end of your Django middleware in `settings.py`:
    
    ```python
    MIDDLEWARE_CLASSES.append("bugsnag.django.middleware.BugsnagMiddleware")
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


Sending Non-Fatal Exceptions to Bugsnag
---------------------------------------

Fatal exceptions are automatically sent to Bugsnag by the notifier.
If you would like to send non-fatal exceptions to Bugsnag, you should import
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
    user_id = "bob-hoskins",
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

###user_id

A unique identifier for a user affected by this event. This could be 
any distinct identifier that makes sense for your application. 
In Django apps, this is automatically set to the username of the current user,
or the remote ip address.

```python
bugsnag.configure_request(user_id = "bob-hoskins")
```

###session_data

The data associated with the current session.
In Django apps, this is automatically populated with the current session
data from the `SessionMiddleware`.

```python
bugsnag.configure_request(session_data = {"default": "/users"})
```

###environment_data

The data associated with the current environment.
In Django apps, this is automatically populated with relevant environment
data automatically.

```python
bugsnag.configure_request(environment_data = {"user-agent": "Mozilla"})
```

###request_data

The data associated with the current request. 
In Django apps, this is automatically populated with the current request
data from the `HttpRequest` object.

```python
bugsnag.configure_request(request_data = {"path": "/users"})
```

###extra_data

A dictionary containing any further data you wish to attach to exceptions.
This data will be displayed in the "Extra Data" tab on your Bugsnag dashboard.

```python
bugsnag.configure_request(extra_data = {"user_type": "admin"})
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
-   Run the tests using [nosetests](https://nose.readthedocs.org/)
-   [Make a pull request](https://help.github.com/articles/using-pull-requests)
-   Thanks!


License
-------

The Bugsnag python notifier is free software released under the MIT License. 
See [LICENSE.txt](https://github.com/bugsnag/bugsnag-python/blob/master/LICENSE.txt) for details.
