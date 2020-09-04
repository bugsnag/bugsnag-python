import bugsnag
import pytest
import django
from django.contrib.auth.models import User
from django.test import Client
try:
    from django.template.exceptions import TemplateSyntaxError
    template_error_class = 'django.template.exceptions.TemplateSyntaxError'
except ImportError:
    from django.template.base import TemplateSyntaxError
    template_error_class = 'django.template.base.TemplateSyntaxError'

from django.conf import settings

from tests.utils import MissingRequestError

# All tests will be treated as marked.
pytestmark = [pytest.mark.django_db]


def pytest_configure(bugsnag_server):
    settings.configure(BUGSNAG={
        'endpoint': bugsnag_server.url,
        'session_endpoint': bugsnag_server.url,
    })


@pytest.fixture
def django_client():
    client = Client()
    User.objects.create_user(
        username='test',
        email='test@example.com',
        password='hunter2')

    yield client

    client.logout()
    User.objects.all().delete()


def test_notify(bugsnag_server, django_client):
    response = django_client.get('/notes/handled-exception/?foo=strawberry')
    assert response.status_code == 200

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'notes.views.handle_notify'
    assert event['severityReason'] == {'type': 'handledException'}
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert 'environment' not in payload['events'][0]['metaData']
    assert event['metaData']['request'] == {
        'method': 'GET',
        'url': 'http://testserver/notes/handled-exception/?foo=strawberry',
        'path': '/notes/handled-exception/',
        'POST': {},
        'encoding': None,
        'GET': {'foo': ['strawberry']}
    }
    assert event['user'] == {}
    assert exception['errorClass'] == 'KeyError'
    assert exception['message'] == "'nonexistent-item'"
    assert exception['stacktrace'][0] == {
        'code': {
             '39': 'def handle_notify(request):',
             '40': '    items = {}',
             '41': '    try:',
             '42': '        print("item: {}" % items["nonexistent-item"])',
             '43': '    except KeyError as e:',
             '44': "        bugsnag.notify(e, unhappy='nonexistent-file')",
             '45': '',
        },
        'file': 'notes/views.py',
        'inProject': True,
        'lineNumber': 42,
        'method': 'handle_notify',
    }


def test_enable_environment(bugsnag_server, django_client):
    bugsnag.configure(send_environment=True)
    response = django_client.get('/notes/handled-exception/?foo=strawberry')
    assert response.status_code == 200

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    assert event['metaData']['environment']['REQUEST_METHOD'] == 'GET'


def test_notify_custom_info(bugsnag_server, django_client):
    django_client.get('/notes/handled-exception-custom/')
    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'custom_info'
    assert event['severityReason'] == {'type': 'userSpecifiedSeverity'}
    assert event['severity'] == 'info'


def test_notify_post_body(bugsnag_server, django_client):
    response = django_client.post('/notes/handled-exception/',
                                  '{"foo": "strawberry"}',
                                  content_type='application/json')
    assert response.status_code == 200

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'notes.views.handle_notify'
    assert event['severityReason'] == {'type': 'handledException'}
    assert event['severity'] == 'warning'
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert event['metaData']['request'] == {
        'method': 'POST',
        'url': 'http://testserver/notes/handled-exception/',
        'path': '/notes/handled-exception/',
        'GET': {},
        'encoding': None,
        'POST': {'foo': 'strawberry'}
    }
    assert event['user'] == {}
    assert exception['errorClass'] == 'KeyError'
    assert exception['message'] == "'nonexistent-item'"
    assert exception['stacktrace'][0] == {
        'code': {
             '39': 'def handle_notify(request):',
             '40': '    items = {}',
             '41': '    try:',
             '42': '        print("item: {}" % items["nonexistent-item"])',
             '43': '    except KeyError as e:',
             '44': "        bugsnag.notify(e, unhappy='nonexistent-file')",
             '45': '',
        },
        'file': 'notes/views.py',
        'inProject': True,
        'lineNumber': 42,
        'method': 'handle_notify',
    }


def test_unhandled_exception(bugsnag_server, django_client):
    with pytest.raises(RuntimeError):
        django_client.get('/notes/unhandled-crash/')

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'crash'
    assert event['severityReason'] == {
        'type': 'unhandledExceptionMiddleware',
        'attributes':  {'framework': 'Django'}
    }
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert event['metaData']['request'] == {
        'method': 'GET',
        'url': 'http://testserver/notes/unhandled-crash/',
        'path': '/notes/unhandled-crash/',
        'POST': {},
        'encoding': None,
        'GET': {}
    }
    assert event['user'] == {}
    assert exception['errorClass'] == 'RuntimeError'
    assert exception['message'] == 'failed to return in time'
    assert exception['stacktrace'][0] == {
        'method': 'unhandled_crash',
        'file': 'notes/views.py',
        'lineNumber': 32,
        'inProject': True,
        'code': {
            '29': '',
            '30': '',
            '31': 'def unhandled_crash(request):',
            '32': "    raise RuntimeError('failed to return in time')",
            '33': '',
            '34': '',
            '35': 'def unhandled_crash_in_template(request):',
        },
    }
    assert exception['stacktrace'][1]['inProject'] is False


def test_unhandled_exception_in_template(bugsnag_server, django_client):
    with pytest.raises(TemplateSyntaxError):
        django_client.get('/notes/unhandled-template-crash/')

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'notes.views.unhandled_crash_in_template'
    assert event['severityReason'] == {
        'type': 'unhandledExceptionMiddleware',
        'attributes':  {'framework': 'Django'}
    }
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert event['metaData']['request'] == {
        'method': 'GET',
        'url': 'http://testserver/notes/unhandled-template-crash/',
        'path': '/notes/unhandled-template-crash/',
        'POST': {},
        'encoding': None,
        'GET': {}
    }
    assert event['user'] == {}
    assert exception['errorClass'] == template_error_class
    assert 'idunno()' in exception['message']


def test_ignores_http404(bugsnag_server, django_client):
    response = django_client.get('/notes/missing_route/')
    assert response.status_code == 404

    with pytest.raises(MissingRequestError):
        bugsnag_server.wait_for_request()

    assert len(bugsnag_server.received) == 0


def test_report_error_from_http404handler(bugsnag_server, django_client):
    with pytest.raises(Exception):
        django_client.get('/notes/poorly-handled-404')

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'GET /notes/poorly-handled-404'
    assert event['severityReason'] == {
        'type': 'unhandledExceptionMiddleware',
        'attributes':  {'framework': 'Django'}
    }
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert event['metaData']['request'] == {
        'method': 'GET',
        'url': 'http://testserver/notes/poorly-handled-404',
        'path': '/notes/poorly-handled-404',
        'POST': {},
        'encoding': None,
        'GET': {}
    }
    assert exception['errorClass'] == 'Exception'
    assert exception['message'] == 'nah'
    assert exception['stacktrace'][0] == {
        'method': 'handler404',
        'file': 'todo/urls.py',
        'lineNumber': 11,
        'inProject': True,
        'code': {
            '8': '',
            '9': 'def handler404(request, *args, **kwargs):',
            '10': "    if 'poorly-handled-404' in request.path:",
            '11': "        raise Exception('nah')",
            '12': '',
            '13': "    response = HttpResponseNotFound('Terrible happenings!',",  # noqa: E501
            '14': "                                    content_type='text/plain')",  # noqa: E501
        },
    }


def test_notify_appends_user_data(bugsnag_server, django_client):
    django_client.login(username='test', password='hunter2')

    response = django_client.get('/notes/handled-exception/?foo=strawberry')
    assert response.status_code == 200

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'notes.views.handle_notify'
    assert event['severityReason'] == {'type': 'handledException'}
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert event['metaData']['custom']['unhappy'] == 'nonexistent-file'
    assert event['metaData']['request'] == {
        'method': 'GET',
        'url': 'http://testserver/notes/handled-exception/?foo=strawberry',
        'path': '/notes/handled-exception/',
        'POST': {},
        'encoding': None,
        'GET': {'foo': ['strawberry']}
    }
    assert event['user'] == {'email': 'test@example.com', 'id': 'test'}
    assert exception['errorClass'] == 'KeyError'
    assert exception['message'] == "'nonexistent-item'"
    assert exception['stacktrace'][0] == {
        'code': {
             '39': 'def handle_notify(request):',
             '40': '    items = {}',
             '41': '    try:',
             '42': '        print("item: {}" % items["nonexistent-item"])',
             '43': '    except KeyError as e:',
             '44': "        bugsnag.notify(e, unhappy='nonexistent-file')",
             '45': '',
        },
        'file': 'notes/views.py',
        'inProject': True,
        'lineNumber': 42,
        'method': 'handle_notify',
    }


def test_crash_appends_user_data(bugsnag_server, django_client):
    django_client.login(username='test', password='hunter2')

    with pytest.raises(RuntimeError):
        django_client.get('/notes/unhandled-crash/')

    bugsnag_server.wait_for_request()
    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]

    assert payload['apiKey'] == 'a05afff2bd2ffaf0ab0f52715bbdcffd'
    assert event['context'] == 'crash'
    assert event['severityReason'] == {
        'type': 'unhandledExceptionMiddleware',
        'attributes':  {'framework': 'Django'}
    }
    assert event['device']['runtimeVersions']['django'] == django.__version__
    assert event['metaData']['request'] == {
        'method': 'GET',
        'url': 'http://testserver/notes/unhandled-crash/',
        'path': '/notes/unhandled-crash/',
        'POST': {},
        'encoding': None,
        'GET': {}
    }
    assert event['user'] == {'email': 'test@example.com', 'id': 'test'}
    assert exception['errorClass'] == 'RuntimeError'
    assert exception['message'] == 'failed to return in time'
    assert exception['stacktrace'][0] == {
        'method': 'unhandled_crash',
        'file': 'notes/views.py',
        'lineNumber': 32,
        'inProject': True,
        'code': {
            '29': '',
            '30': '',
            '31': 'def unhandled_crash(request):',
            '32': "    raise RuntimeError('failed to return in time')",
            '33': '',
            '34': '',
            '35': 'def unhandled_crash_in_template(request):',
        },
    }
    assert exception['stacktrace'][1]['inProject'] is False
