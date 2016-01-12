from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'demo.views.index'),
    url(r'^crash/$', 'demo.views.crash'),
    url(r'^crash_with_callback/$', 'demo.views.crash_with_callback'),
    url(r'^notify/$', 'demo.views.notify'),
    url(r'^notify_meta/$', 'demo.views.notify_meta'),
    url(r'^context/$', 'demo.views.context'),
    url(r'^severity/$', 'demo.views.severity'),
)
