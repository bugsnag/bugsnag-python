from django.conf.urls import url
from notes import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^notes/unhandled-crash/$', views.unhandled_crash, name='crash'),
    url(r'^notes/unhandled-template-crash/$',
        views.unhandled_crash_in_template),
    url(r'^notes/handled-exception/$', views.handle_notify),
    url(r'^notes/handled-exception-custom/$', views.handle_notify_custom_info),
]
