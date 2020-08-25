from django.conf.urls import include, url
from django.http import HttpResponseNotFound

urlpatterns = [
    url(r'^notes/', include('notes.urls'))
]


def handler404(request, *args, **kwargs):
    if 'poorly-handled-404' in request.path:
        raise Exception('nah')

    response = HttpResponseNotFound('Terrible happenings!',
                                    content_type='text/plain')
    response.status_code = 404
    return response
