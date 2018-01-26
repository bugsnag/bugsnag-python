from django.conf.urls import url
from demo.views import (index, crash, crash_with_callback, notify,
                        context, notify_meta)

urlpatterns = [
    url(r'^$', index),
    url(r'^crash/$', crash),
    url(r'^crash_with_callback/$', crash_with_callback),
    url(r'^notify/$', notify),
    url(r'^notify_meta/$', notify_meta),
    url(r'^context/$', context),
]
