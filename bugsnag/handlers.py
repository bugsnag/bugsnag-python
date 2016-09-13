from __future__ import division, print_function, absolute_import

import logging
import warnings

import bugsnag


class BugsnagHandler(logging.Handler, object):
    def __init__(self, api_key=None, extra_fields=None, client=None):
        """
        Creates a new handler which sends records to Bugsnag
        """
        super(BugsnagHandler, self).__init__()
        self.client = client
        self.callbacks = [self.extract_metadata, self.extract_severity]

        if api_key is not None:
            warnings.warn('api_key is deprecated in favor of using a client '
                          'to set the correct API key '
                          'and will be removed in a future release.',
                          DeprecationWarning)

            def add_api_key(record, options):
                options['api_key'] = api_key

            self.add_callback(add_api_key)

        if extra_fields is not None:
            warnings.warn('extra_fields is deprecated in favor of using a '
                          'client and changing notification options using '
                          'add_callback. '
                          'extra_fields will be removed in a future release.',
                          DeprecationWarning)

            def add_extra_fields(record, options):
                if 'meta_data' not in options:
                    options['meta_data'] = {}

                for section in extra_fields:
                    if section not in options['meta_data']:
                        options['meta_data'][section] = {}

                    for field in extra_fields[section]:
                        if hasattr(record, field):
                            attr = getattr(record, field)
                            options['meta_data'][section][field] = attr

            self.add_callback(add_extra_fields)

    def emit(self, record):
        """
        Outputs the record to Bugsnag
        """
        options = {}

        for callback in self.callbacks:
            try:
                callback(record, options)
            except Exception as e:
                bugsnag.logger.error('Failed to run handler callback %s', e)

        client = self.client or bugsnag.legacy.default_client

        if record.exc_info:
            client.notify_exc_info(*record.exc_info, **options)
        else:
            # Create exception type dynamically, to prevent bugsnag.handlers
            # being prepended to the exception name due to class name
            # detection in utils. Because we are messing with the module
            # internals, we don't really want to expose this class anywhere
            level_name = record.levelname or "Message"
            exc_type = type('Log' + level_name, (Exception, ), {})
            exc = exc_type(record.getMessage())
            exc.__module__ = None

            client.notify(exc, **options)

    def add_callback(self, callback):
        """
        Add a new callback to be invoked after an log message is sent but
        before it is sent to Bugsnag. Each callback is invoked with the
        LogRecord and options to be sent to notify.
        """
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        """
        Remove a callback
        """
        self.callbacks.remove(callback)

    def clear_callbacks(self):
        """
        Clear all callbacks
        """
        del self.callbacks[:]

    def extract_severity(self, record, options):
        """
        Convert log record level into severity levels
        """
        levelno = record.levelno or logging.WARNING

        if levelno >= logging.ERROR:
            options['severity'] = 'error'
        elif levelno >= logging.WARNING:
            options['severity'] = 'warning'
        else:
            options['severity'] = 'info'

    def extract_metadata(self, record, options):
        """
        Extract log record fields into error report metadata
        """
        record_fields = ('asctime', 'created', 'levelname', 'levelno', 'msecs',
                         'name', 'process', 'processName', 'relativeCreated',
                         'thread', 'threadName',)

        extra_data = {}
        for field in record_fields:
            if hasattr(record, field):
                extra_data[field] = getattr(record, field)

        if 'meta_data' not in options:
            options['meta_data'] = {}

        options['meta_data']['extra data'] = extra_data
