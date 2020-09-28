import bugsnag

from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse(b'Some content!')


"""
(some nonsense goes here)















"""


def unhandled_crash(request):
    raise RuntimeError('failed to return in time')


def unhandled_crash_in_template(request):
    return render(request, 'notes/broken.html')


def handle_notify(request):
    items = {}
    try:
        print("item: {}" % items["nonexistent-item"])
    except KeyError as e:
        bugsnag.notify(e, unhappy='nonexistent-file')

    return HttpResponse(b'everything is fine!', content_type='text/plain')


def handle_notify_custom_info(request):
    bugsnag.notify(Exception('something bad happened'), severity='info',
                   context='custom_info')
    return HttpResponse('nothing to see here', content_type='text/plain')


def request_inspection(event):
    event.context = event.request.GET['user_id']


def handle_crash_callback(request):
    bugsnag.before_notify(request_inspection)
    terrible_event()


def terrible_event():
    raise RuntimeError('I did something wrong')
