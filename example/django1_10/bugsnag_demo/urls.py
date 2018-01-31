from django.conf.urls import url
from demo.views import (index, crash, crash_with_callback, handled,
                        context, notify_meta)

urlpatterns = [
    url(r'^$', index),
    url(r'^crash/$', crash),
    url(r'^crashcallback/$', crash_with_callback),
    url(r'^handled/$', handled),
    url(r'^notifywithcontext/$', context),
    url(r'^notifywithmetadata/$', notify_meta),
]
