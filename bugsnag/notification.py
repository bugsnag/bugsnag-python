import warnings

from bugsnag.event import Event


__all__ = ('Notification',)


class Notification(Event):
    def __init__(self, exception, config, request_config, **options):
        warnings.warn('The Notification class has been deprecated in favor ' +
                      'of bugsnag.event.Event and will be removed in a ' +
                      'future release.', DeprecationWarning)
        super().__init__(exception, config, request_config, **options)
