import bugsnag

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views import generic
from django.utils import timezone
from django.urls import reverse

from .models import Note


class IndexView(generic.ListView):
    template_name = 'notes/index.html'
    context_object_name = 'latest_notes_list'

    def get_queryset(self):
        return Note.objects.order_by('-create_date')[:5]


class DetailView(generic.DetailView):
    model = Note


def add_note(request):
    note_text = request.POST['note_text']
    note = Note(note_text=note_text, create_date=timezone.now())
    note.save()
    return HttpResponseRedirect(reverse('detail', args=(note.id,)))


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

    return HttpResponse('everything is fine!', content_type='text/plain')


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


def unhandled_crash_chain(request):
    try:
        unhandled_crash(request)
    except RuntimeError as e:
        raise Exception('corrupt timeline detected') from e
