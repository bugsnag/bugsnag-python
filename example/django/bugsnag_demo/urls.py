from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'bugsnag_demo.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', 'demo.views.index'),
    url(r'^crash/$', 'demo.views.crash'),
    url(r'^crash_with_callback/$', 'demo.views.crash_with_callback'),
    url(r'^notify/$', 'demo.views.notify'),
    url(r'^notify_meta/$', 'demo.views.notify_meta'),
    url(r'^context/$', 'demo.views.context'),
    url(r'^severity/$', 'demo.views.severity'),
    url(r'^admin/', include(admin.site.urls)),
)
