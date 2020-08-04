from django.urls import include, path
from django.http import HttpResponseNotFound

urlpatterns = [
    path('notes/', include('notes.urls'))
]


def handler404(request, exception):
    if 'poorly-handled-404' in request.path:
        raise Exception('nah')

    response = HttpResponseNotFound(b'Terrible happenings!',
                                    content_type='text/plain')
    response.status_code = 404
    return response
