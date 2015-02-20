Changelog
=========

2.3.0
-----
-   Add add_metadata_tab method
-   Fix Flask integration overriding user information

2.2.0
-----
-   Optionally send a snippet of code along with each frame in the stacktrace
-   Default to https:// for reports.


2.1.0
-----
-   Allow custom meta-data when using the Bugsnag log handler (thanks @lwcolton!)
-   Update flask support for python 3.4 (thanks @stas!)
-   Show json post body for flask requests (thanks @stas!)

2.0.2
-----
-   Better logging support
-   More robustness for notifies during shutdown
-   Call close() on WSGI apps that are only iterable, not iterators

2.0.1
-----
-   Now works on Python 3.2

2.0.0
-----
-   Read request-local settings in bugsnag.notify
-   Add support for before_notify callbacks
-   Avoid truncating values when unnecessary
-   Send user data to bugsnag for django

1.5.0
-----
-   Send 'severity' of error to Bugsnag
-   Add 'payloadVersion'

1.4.0
-----
-   Make params_filter configuration work

1.3.2
-----
-   Allow custom groupingHash

1.3.1
-----
-   Send hostname to Bugsnag

1.3.0
-----
-   Added celery integration

1.2.7
-----
-   Configure the log handler in the constructor for when called from cron job.

1.2.6
-----
-   Read the API key from the environment for Heroku users
-   Best guess a project_root for a sensible default

1.2.5
-----
-   Add blinker as a dependency, makes using Bugsnag with Flask easier

1.2.4
-----
-   Removed automatic userId population from username in django, to avoid a
    database lookup

1.2.3
-----
-   Fix cookies bug in Tornado apps

1.2.2
-----
-   Added support for Tornado apps

1.2.1
-----
-   Additional protection for bad string encodings

1.2.0
-----
-   Fixed issue when non-unicode data was passed in metadata
-   Filters are now applied for substring matches ("password" will now also
    match "confirm_password")
-   Ignore django.http.Http404 exceptions by default when using
    django middleware

1.1.2
-----
-   Log trace when HTTP exception

1.1.1
------
-   Log the trace when theres an exception notifying
