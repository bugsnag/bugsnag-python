Changelog
=========

## 3.0.0 (2016-10-31)

This is a major release adding a number of new features and deprecating some
lesser used parts of the library.

## Enhancements

* Add compatibility with Django 1.10
  [Jonny Pickett](https://github.com/jonnypickett)
  [#108](https://github.com/bugsnag/bugsnag-python/pull/108)

* Support customizing delivery and sending error reports using
  [requests](http://docs.python-requests.org/en/master/).

  The new `Delivery` class is a generic way of sending a serialized payload to
  Bugsnag. The `Configuration` class now has a `delivery` property which should
  be an instance of `Delivery`. By default, if requests is installed, reports
  are sent via `bugsnag.delivery.RequestsDelivery` rather than
  `bugsnag.delivery.UrllibDelivery`.

  To enforce using urllib2/urllib3, use `UrllibDelivery`:

  ```python
  from bugsnag.delivery import UrllibDelivery

  bugsnag.configure(delivery=UrllibDelivery())
  ```

  To use a custom `Delivery`:

  ```python
  from bugsnag.delivery import Delivery

  class SomeSpecialDelivery(Delivery):

      def deliver(self, config, payload):
          send_to_my_queue(config.get_endpoint(), config.proxy_host, payload)

  bugsnag.configure(delivery=SomeSpecialDelivery())
  ```

  [Graham Campbell](https://github.com/GrahamCampbell)
  [Delisa Mason](https://github.com/kattrali)
  [#86](https://github.com/bugsnag/bugsnag-python/pull/86)

* Support multiple clients in a single environment using `bugsnag.Client`. A new
  client can be initialized using a `Configuration` or options passed to
  `Client()`. By default, a client is installed as the system exception hook.
  To disable this behavior, set `install_sys_hook` to `False`.

  ```python
  client = Client(api_key='...')
  ```

  ```python
  config = Configuration(api_key='...')
  client = Client(config)
  ```
  [Kyle Fuller](https://github.com/kylef)
  [#101](https://github.com/bugsnag/bugsnag-python/pull/101)

* Support running a block of code within a client's context. Any exception
  raised will be reported.

  ```python
  with client.capture():
      raise Exception('an exception reported to Bugsnag then reraised')
  ```

  Specific types of exceptions can be captured by adding `exceptions` as a
  tuple.

  ```python
  with client.capture((TypeError,)):
      raise Exception('an exception which does not get captured')
  ```

  Additional options can be passed to th resulting error report, such as
  attached metadata or severity.

  ```python
  with client.capture(account_id='123', severity='info'):
      raise Exception('failed to validate record')
  ```

  Functions can be decorated to capture any exceptions thrown during execution.

  ```python
  @client.capture
  def foo():
      raise Exception('an exception passed to Bugsnag then reraised')

  @client.capture((TypeError,))
  def bar():
      raise Exception('an exception which does not get captured')

  @client.capture(test_slice='B')
  def baz():
      raise Exception('an exception passed to Bugsnag then reraised')
  ```

  [Kyle Fuller](https://github.com/kylef)
  [Delisa Mason](https://github.com/kattrali)
  [#101](https://github.com/bugsnag/bugsnag-python/pull/101)

* Support creating a log handler from a client, and forwarding logged messages
  to Bugsnag.

  ```python
  client = Client(api_key='...')
  logger = logging.getLogger(__name__)

  logger.addHandler(client.log_handler())
  ```

  Log messages can also be customized using additional information from the
  log record and callbacks:

  ```python
  client = Client(api_key='...')
  logger = logging.getLogger(__name__)
  handler = client.log_handler()

  def add_extra_info(record, options):
      if 'meta_data' not in options:
          options['meta_data'] = {}

      options['meta_data']['stats'] = {
        'account_id': record.account_id,
        'ab_test_slice': record.slice_name
      }

  handler.add_callback(add_extra_info)
  logger.addHandler(handler)
  ```

  `BugsnagHandler` argument `api_key` was deprecated as a part of this change.

  [Delisa Mason](https://github.com/kattrali)
  [#103](https://github.com/bugsnag/bugsnag-python/pull/103)

* Replace existing logging with a logger. Logs from bugsnag can now be
  controlled by setting the log level of `logging.getLogger('bugsnag')`.
  [Kyle Fuller](https://github.com/kylef)
  [#95](https://github.com/bugsnag/bugsnag-python/pull/95)

* Wrap non-Exception objects passed to `notify()` in a `RuntimeError`
  [Delisa Mason](https://github.com/kattrali)
  [#98](https://github.com/bugsnag/bugsnag-python/pull/98)

### Bug fixes

* Fix proxy configuration setting a global opener
  [Kyle Fuller](https://github.com/kylef)
  [#97](https://github.com/bugsnag/bugsnag-python/pull/97)

* Fix dropped reports during fatal errors occuring before threads join
  [Delisa Mason](https://github.com/kattrali)
  [#99](https://github.com/bugsnag/bugsnag-python/pull/99)

* Fix missing error reports when invoking a function decorated with a Bugsnag
  client using the wrong arguments
  [Delisa Mason](https://github.com/kattrali)
  [#110](https://github.com/bugsnag/bugsnag-python/pull/110)


## 2.5.2 (2016-08-19)

### Enhancements

* Log exception message when notifications fail to send

### Bug Fixes

* Improve recursion handling in metadata parsing

## 2.5.1 (2016-08-12)

### Bug Fixes

* Fix setting `api_key` and `grouping_hash` from `notify()` or `before_notify()`
* Fix merge behavior when overriding metadata from `notify()`

## 2.5.0 (2016-06-14)

### Enhancements

* Add support for proxied connections to Bugsnag
  [Tomas Edwardsson](https://github.com/tomas-edwardsson)
  [#79](https://github.com/bugsnag/bugsnag-python/pull/79)

### Bug Fixes

* Fix an issue where the package version is marked as "unknown"
  [Kyle Fuller](https://github.com/kylef)
  [#83](https://github.com/bugsnag/bugsnag-python/pull/83)

* Fix an issue where request metadata is not sent when not using
  SessionMiddleware in Django

## 2.4.0 (2016-01-18)

### Enhancements

* Add synchronous upload mode
  [Tuomas Peippo](https://github.com/tume)
  [#67](https://github.com/bugsnag/bugsnag-python/pull/67)
  [#71](https://github.com/bugsnag/bugsnag-python/pull/71)

* Add stacktraces to middleware exception logging
  [Delisa Mason](https://github.com/kattrali)
  [#77](https://github.com/bugsnag/bugsnag-python/pull/77)

* Remove cookie logging from WSGI and Flask configurations
  [Delisa Mason](https://github.com/kattrali)

### Bug Fixes

* Remove use of deprecated `request.REQUEST` attribute in favor of `GET`/`POST`
  [Delisa Mason](https://github.com/kattrali)
  [#69](https://github.com/bugsnag/bugsnag-python/pull/69)

* Fix user attribute logging for Django custom authentication setups
  [Delisa Mason](https://github.com/kattrali)
  [#76](https://github.com/bugsnag/bugsnag-python/pull/76)
  [#78](https://github.com/bugsnag/bugsnag-python/pull/78)


2.3.1
-----
-   Redact HTTP_COOKIE and HTTP_AUTHORIZATION by default

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
