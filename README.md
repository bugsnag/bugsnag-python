# Bugsnag exception reporter for Python
[![Build status](https://travis-ci.org/bugsnag/bugsnag-python.svg?branch=master)](https://travis-ci.org/bugsnag/bugsnag-python)
[![Documentation](https://img.shields.io/badge/documentation-latest-blue.svg)](https://docs.bugsnag.com/platforms/python/)

The Bugsnag exception reporter for Python automatically detects and reports
exceptions thrown your **Django**, **WSGI**, **Tornado**, **Flask** or
**plain Python** app.  Any uncaught exceptions will trigger a notification to be
sent to your Bugsnag project.


## Features

* Automatically report unhandled exceptions and crashes
* Report handled exceptions
* Attach user information and custom diagnostic data to determine how many
  people are affected by a crash


## Getting started

1. [Create a Bugsnag account](https://bugsnag.com)
2. Complete the instructions in the
   [integration guide](https://docs.bugsnag.com/platforms/python/)
3. Report handled exceptions using
   [`bugsnag.notify()`](https://docs.bugsnag.com/platforms/python/reporting-handled-errors/)
4. Customize your integration using the
   [configuration options](https://docs.bugsnag.com/platforms/python/configuration-options/)

## Support

* Check out the [configuration options](https://docs.bugsnag.com/platforms/python/configuration-options/)
* [Search open and closed issues](https://github.com/bugsnag/bugsnag-python/issues?utf8=✓&q=is%3Aissue) for similar problems
* [Report a bug or request a feature](https://github.com/bugsnag/bugsnag-python/issues/new)


## Contributing

All contributors are welcome! For information on how to build, test,
and release, see our [contributing guide](CONTRIBUTING.md).


## License

The Bugsnag Python library is free software released under the MIT License.
See [LICENSE.txt](LICENSE.txt) for details.
