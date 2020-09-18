from typing import Dict, Any

from bugsnag.configuration import RequestConfiguration

import bugsnag

__all__ = []


def configure(**options):
    """
    Configure the Bugsnag notifier application-wide settings.
    """
    return bugsnag.default_client.configuration.configure(**options)


def configure_request(**options):
    """
    Configure the Bugsnag notifier per-request settings.
    """
    RequestConfiguration.get_instance().configure(**options)


def add_metadata_tab(tab_name: str, data: Dict[str, Any]):
    """
    Add metaData to the tab

    bugsnag.add_metadata_tab("user", {"id": "1", "name": "Conrad"})
    """
    meta_data = RequestConfiguration.get_instance().meta_data
    if tab_name not in meta_data:
        meta_data[tab_name] = {}

    meta_data[tab_name].update(data)


def clear_request_config():
    """
    Clears the per-request settings.
    """
    RequestConfiguration.clear()


def send_sessions():
    """
    Delivers all currently undelivered sessions to Bugsnag
    """
    default_client.session_tracker.send_sessions()


def before_notify(callback):
    """
    Add a callback to be called before bugsnag is notified

    This can be used to alter the event before sending it to Bugsnag.
    """
    bugsnag.default_client.configuration.middleware.before_notify(callback)
