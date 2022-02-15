from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'unhandled-crash/', views.unhandled_crash, name='crash'),
    url(r'unhandled-crash-chain/', views.unhandled_crash_chain),
    url(r'unhandled-template-crash/',
        views.unhandled_crash_in_template),
    url(r'handled-exception/', views.handle_notify),
    url(r'handled-exception-custom/', views.handle_notify_custom_info),
    url(r'crash-with-callback/', views.handle_crash_callback),
]
