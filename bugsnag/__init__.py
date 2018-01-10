import sys
import logging

from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification
from bugsnag.client import Client
from bugsnag.legacy import (configuration, configure, configure_request,
                            add_metadata_tab, clear_request_config, notify,
                            auto_notify, before_notify, start_session,
                            send_sessions)

__all__ = ('Client', 'Notification', 'Configuration', 'RequestConfiguration',
           'configuration', 'configure', 'configure_request',
           'add_metadata_tab', 'clear_request_config', 'notify',
           'auto_notify', 'before_notify', 'start_session',
           'send_sessions')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    '%(asctime)s - [%(name)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
