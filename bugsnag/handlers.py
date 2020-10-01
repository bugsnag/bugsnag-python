import logging
from logging import LogRecord
from typing import Dict

import bugsnag


__all__ = ('BugsnagHandler',)


class BugsnagHandler(logging.Handler, object):
    def __init__(self, client=None, extra_fields=None):
        """
        Creates a new handler which sends records to Bugsnag
        """
        super(BugsnagHandler, self).__init__()
        self.client = client
        self.custom_metadata_fields = extra_fields
        self.callbacks = [self.extract_default_metadata,
                          self.extract_custom_metadata,
                          self.extract_severity]

    def emit(self, record: LogRecord):
        """
        Outputs the record to Bugsnag
        """
        if hasattr(bugsnag, '__path__'):
            paths = getattr(bugsnag, '__path__')
            for path in paths:
                if path in record.pathname:
                    return

        options = {
            'metadata': {},
            'unhandled': False,
            'severity_reason': {
                'type': 'log',
                'attributes': {
                    'level': record.levelname
                }
            }
        }

        for callback in self.callbacks:
            try:
                callback(record, options)
            except Exception as e:
                bugsnag.logger.error('Failed to run handler callback %s', e)

        client = self.client or bugsnag.legacy.default_client

        if 'exception' in options:
            exception = options.pop('exception')
            if isinstance(exception, Exception):
                client.notify(exception, **options)
                return
            else:
                try:
                    metadata = options['metadata']
                    if isinstance(metadata, dict):
                        metadata['exception'] = exception
                except TypeError:
                    # Means options['metadata'] is no longer a dictionary
                    pass

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

    def extract_severity(self, record: LogRecord, options: Dict):
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

    def extract_custom_metadata(self, record: LogRecord, options: Dict):
        """
        Append the contents of selected fields of a record to the metadata
        of a report
        """
        if self.custom_metadata_fields is None:
            return

        if 'metadata' not in options:
            options['metadata'] = {}

        for section in self.custom_metadata_fields:
            if section not in options['metadata']:
                options['metadata'][section] = {}

            for field in self.custom_metadata_fields[section]:
                if hasattr(record, field):
                    attr = getattr(record, field)
                    options['metadata'][section][field] = attr

    def extract_default_metadata(self, record: LogRecord, options: Dict):
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

        if 'metadata' not in options:
            options['metadata'] = {}

        options['metadata']['extra data'] = extra_data
