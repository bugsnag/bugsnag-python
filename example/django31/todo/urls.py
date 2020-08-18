from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('notes/', include('notes.urls'))
]
