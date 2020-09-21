import sys
import logging

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification
from bugsnag.event import Event
from bugsnag.client import Client
from bugsnag.legacy import (configuration, configure, configure_request,
                            add_metadata_tab, clear_request_config, notify,
                            auto_notify, before_notify, start_session,
                            auto_notify_exc_info)

__all__ = ('Client', 'Event', 'Configuration', 'RequestConfiguration',
           'configuration', 'configure', 'configure_request',
           'add_metadata_tab', 'clear_request_config', 'notify',
           'auto_notify', 'before_notify', 'start_session',
           'auto_notify_exc_info',
           'Notification')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    '%(asctime)s - [%(name)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
