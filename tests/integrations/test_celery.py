from contextlib import contextmanager
import pytest
import celery
from celery import shared_task
from celery.signals import task_failure
from bugsnag.celery import connect_failure_handler, failure_handler
from tests.utils import MissingRequestError


@pytest.fixture(scope='function')
def celery_config():
    return {
        'broker_url': 'memory://',
        'result_backend': 'rpc',
    }


@contextmanager
def celery_failure_handler():
    """
    The bugsnag celery integration works by listening to the celery
    task_failure signal and sending an event when the signal is received.

    This context manages the signal connection and ensures that error handling
    does not occur across separate tests.
    """
    connect_failure_handler()
    try:
        yield
    finally:
        task_failure.disconnect(failure_handler)


def test_app_task_operation(celery_app, celery_worker, bugsnag_server):
    """
    Configuring bugsnag should not interfere with tasks succeeding normally
    """

    @celery_app.task
    def square(x):
        return x * x

    celery_worker.reload()

    with celery_failure_handler():
        assert square.delay(3).get(timeout=1) == 9

    with pytest.raises(MissingRequestError):
        bugsnag_server.wait_for_request()

    assert len(bugsnag_server.received) == 0


def test_app_task_failure(celery_app, celery_worker, bugsnag_server):
    """
    Bugsnag should capture failures in app tasks
    """

    def validate(x, y):
        raise FloatingPointError('expect the unexpected!')

    @celery_app.task
    def cube(x):
        return x * x * x

    @celery_app.task
    def divide(x, y):
        if validate(x, y):
            return x / y

    celery_worker.reload()

    with celery_failure_handler():
        # bugsnag should not depend on the result being resolved using get()
        divide.delay(7, 0)
        # other (non-failing) tasks should behave normally
        result = cube.delay(3)
        bugsnag_server.wait_for_request()

    assert len(bugsnag_server.received) == 1
    assert result.get(timeout=1) == 27

    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]
    task = event['metaData']['extra_data']

    assert 'task_id' in task
    assert task['args'] == [7, 0]
    assert event['context'] == 'test_celery.divide'
    assert event['severityReason']['type'] == 'unhandledExceptionMiddleware'
    assert event['severityReason']['attributes'] == {'framework': 'Celery'}
    assert event['device']['runtimeVersions']['celery'] == celery.__version__
    assert exception['errorClass'] == 'FloatingPointError'
    assert exception['message'] == 'expect the unexpected!'
    assert exception['stacktrace'][0]['method'] == 'validate'
    assert exception['stacktrace'][1]['method'] == 'divide'


def test_app_task_failure_result_status(celery_app, celery_worker,
                                        bugsnag_server):
    """
    Bugsnag integration should not suppress normal failure behavior when
    checking the result of a failed task
    """
    def validate(x, y):
        raise FloatingPointError('expect the unexpected!')

    @celery_app.task
    def cube(x):
        return x * x * x

    @celery_app.task
    def divide(x, y):
        if validate(x, y):
            return x / y

    celery_worker.reload()

    with celery_failure_handler():
        failed_result = divide.delay(7, 0)
        result = cube.delay(3)

        with pytest.raises(FloatingPointError):
            # bugsnag should not suppress the exception
            failed_result.get(timeout=1)

    bugsnag_server.wait_for_request()
    assert len(bugsnag_server.received) == 1
    assert result.get(timeout=1) == 27


def test_shared_task_operation(celery_worker, bugsnag_server):
    """
    Configuring bugsnag should not interfere with shared tasks succeeding
    normally
    """

    @shared_task
    def add(x, y):
        return x + y

    celery_worker.reload()

    with celery_failure_handler():
        result = add.delay(2, 2)

        with pytest.raises(MissingRequestError):
            bugsnag_server.wait_for_request()

    assert len(bugsnag_server.received) == 0
    assert result.get(timeout=1) == 4


def test_shared_task_failure(celery_worker, bugsnag_server):
    """
    Bugsnag should capture failures in standalone tasks
    """

    @shared_task
    def divide(x, y, **kwargs):
        return x / y

    celery_worker.reload()

    with celery_failure_handler():
        divide.delay(2, 0, parts='multi', cache=2)

        bugsnag_server.wait_for_request()

    assert len(bugsnag_server.received) == 1

    payload = bugsnag_server.received[0]['json_body']
    event = payload['events'][0]
    exception = event['exceptions'][0]
    task = event['metaData']['extra_data']

    assert 'task_id' in task
    assert task['args'] == [2, 0]
    assert task['kwargs'] == {'parts': 'multi', 'cache': 2}
    assert event['context'] == 'test_celery.divide'
    assert event['severityReason']['type'] == 'unhandledExceptionMiddleware'
    assert event['severityReason']['attributes'] == {'framework': 'Celery'}
    assert event['device']['runtimeVersions']['celery'] == celery.__version__
    assert exception['errorClass'] == 'ZeroDivisionError'
    assert exception['stacktrace'][0]['method'] == 'divide'
