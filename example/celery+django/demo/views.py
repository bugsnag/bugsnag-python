from django.http import HttpResponse

def readme(request):
    return HttpResponse('Hello world')