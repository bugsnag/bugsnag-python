from bugsnag.configuration import Configuration, RequestConfiguration
from bugsnag.notification import Notification
from bugsnag.event import Event
from bugsnag.client import Client
from bugsnag.breadcrumbs import (
    BreadcrumbType,
    Breadcrumb,
    Breadcrumbs,
    OnBreadcrumbCallback
)
from bugsnag.feature_flags import FeatureFlag
from bugsnag.legacy import (configuration, configure, configure_request,
                            add_metadata_tab, clear_request_config, notify,
                            auto_notify, before_notify, start_session,
                            auto_notify_exc_info, logger, leave_breadcrumb,
                            add_on_breadcrumb, remove_on_breadcrumb,
                            add_feature_flag, add_feature_flags,
                            clear_feature_flag, clear_feature_flags)

__all__ = ('Client', 'Event', 'Configuration', 'RequestConfiguration',
           'configuration', 'configure', 'configure_request',
           'add_metadata_tab', 'clear_request_config', 'notify',
           'auto_notify', 'before_notify', 'start_session',
           'auto_notify_exc_info', 'Notification', 'logger',
           'BreadcrumbType', 'Breadcrumb', 'Breadcrumbs',
           'OnBreadcrumbCallback', 'leave_breadcrumb', 'add_on_breadcrumb',
           'remove_on_breadcrumb', 'FeatureFlag', 'add_feature_flag',
           'add_feature_flags', 'clear_feature_flag', 'clear_feature_flags')
