from django.urls import path
from . import views


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('add/', views.add_note, name='add'),
    path('unhandled-crash/', views.unhandled_crash, name='crash'),
    path('unhandled-crash-chain/', views.unhandled_crash_chain),
    path('unhandled-template-crash/', views.unhandled_crash_in_template),
    path('handled-exception/', views.handle_notify),
    path('crash-with-callback/', views.handle_crash_callback),
    path('handled-exception-custom/', views.handle_notify_custom_info),
]
