from django.http import HttpResponse
from demo.tasks import divide, safedivide, reporteddivide, metadivide, contextdivide, severitydivide
import markdown

def readme(request):
    with open('demo/templates/index.md') as fp:
        return HttpResponse(markdown.markdown(fp.read()))

def crash(request):
    divide.delay(1, 0)
    return HttpResponse('The attached celery process should have an error, ' +
        'check <a href="https://bugsnag.com">bugsnag</a> dashboard for errors')

def crashcallback(request):
    reporteddivide.delay(1, 0)
    return HttpResponse('The attached celery process should have an error, ' +
        'it should also have attached additional metadata viewable in the ' +
        'bugsnag dashboard as an additional tag')

def notify(request):
    safedivide.delay(1, 0)
    return HttpResponse('The attached celery process has manually notified ' +
        'bugsnag despite the fact it managed to catch the error')

def notifymeta(request):
    metadivide(1, 0)
    return HttpResponse('The attached celery process has manually notified ' +
        'bugsnag, and included some additional metadata')

def notifycontext(request):
    contextdivide(1, 0)
    return HttpResponse('The attached celery process has manually notified ' +
        'bugsnag, and added a custom context')

def notifyseverity(request):
    severitydivide(1, 0)
    return HttpResponse('The attached celery process has manually notified ' +
        'bugsnag, and set a specific severity level')