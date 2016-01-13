from django.conf.urls import patterns, include, url
from demo.views import (index, crash, crash_with_callback, severity, notify,
                        context, notify_meta)

urlpatterns = patterns('',
    url(r'^$', index),
    url(r'^crash/$', crash),
    url(r'^crash_with_callback/$', crash_with_callback),
    url(r'^notify/$', notify),
    url(r'^notify_meta/$', notify_meta),
    url(r'^context/$', context),
    url(r'^severity/$', severity),
)
