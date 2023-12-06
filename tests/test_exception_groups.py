import bugsnag
import pytest
import sys

from tests import fixtures
from .utils import is_exception_group_supported


# the exceptiongroup package will only define ExceptionGroup on versions <3.11
# on 3.11+ it re-exports the built-in class so even if exceptiongroup is
# installed, the class name won't have the 'exceptiongroup' prefix
if sys.version_info < (3, 11):
    expected_exception_group_class = 'exceptiongroup.ExceptionGroup'
else:
    expected_exception_group_class = 'ExceptionGroup'


@pytest.mark.skipif(
    not is_exception_group_supported,
    reason="requires python 3.11 or the exceptiongroup pacakge"
)
def test_exception_groups_are_unwrapped(bugsnag_server):
    # disable send_code so we can assert against stacktraces more easily
    bugsnag.configure(send_code=False)

    bugsnag.notify(fixtures.exception_group_with_no_cause)

    bugsnag_server.wait_for_event()
    assert bugsnag_server.sent_report_count == 1

    payload = bugsnag_server.events_received[0]['json_body']
    exceptions = payload['events'][0]['exceptions']

    # there should be 1 ExceptionGroup with 4 sub-exceptions
    assert len(exceptions) == 5

    assert exceptions[0] == {
        'message': 'the message of the group (4 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_no_cause',
                'lineNumber': 21,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': '<module>',
                'lineNumber': 25,
                'inProject': True,
                'code': None,
            },
        ],
    }

    expected_sub_exceptions = [
        'Exception',
        'ArithmeticError',
        'NameError',
        'AssertionError',
    ]

    for i, expected in enumerate(expected_sub_exceptions, start=1):
        assert exceptions[i] == {
            'message': 'exception #' + str(i),
            'errorClass': expected,
            'type': 'python',
            'stacktrace': [
                {
                    'file': 'tests/fixtures/exception_groups.py',
                    'method': 'generate_exception',
                    'lineNumber': 15,
                    'inProject': True,
                    'code': None,
                }
            ]
        }


@pytest.mark.skipif(
    not is_exception_group_supported,
    reason="requires python 3.11 or the exceptiongroup pacakge"
)
def test_base_exception_group_subclasses_are_unwrapped(bugsnag_server):
    # disable send_code so we can assert against stacktraces more easily
    bugsnag.configure(send_code=False)

    bugsnag.notify(fixtures.base_exception_group_subclass)

    bugsnag_server.wait_for_event()
    assert bugsnag_server.sent_report_count == 1

    payload = bugsnag_server.events_received[0]['json_body']
    exceptions = payload['events'][0]['exceptions']

    # there should be 1 MyExceptionGroup with 3 sub-exceptions
    assert len(exceptions) == 4

    assert exceptions[0] == {
        'message': 'my very easy method just speeds up (n)making exception groups (3 sub-exceptions)',  # noqa: E501
        'errorClass': 'tests.fixtures.exception_groups.MyExceptionGroup',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_base_exception_group_subclass_with_no_cause',  # noqa: E501
                'lineNumber': 35,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': '<module>',
                'lineNumber': 39,
                'inProject': True,
                'code': None,
            },
        ],
    }

    expected_sub_exceptions = [
        'GeneratorExit',
        'ReferenceError',
        'NotImplementedError',
    ]

    for i, expected in enumerate(expected_sub_exceptions, start=1):
        assert exceptions[i] == {
            'message': 'exception #' + str(i),
            'errorClass': expected,
            'type': 'python',
            'stacktrace': [
                {
                    'file': 'tests/fixtures/exception_groups.py',
                    'method': 'generate_exception',
                    'lineNumber': 15,
                    'inProject': True,
                    'code': None,
                }
            ]
        }


@pytest.mark.skipif(
    not is_exception_group_supported,
    reason="requires python 3.11 or the exceptiongroup pacakge"
)
def test_do_not_recurse_into_sub_exception_groups(bugsnag_server):
    # disable send_code so we can assert against stacktraces more easily
    bugsnag.configure(send_code=False)

    bugsnag.notify(fixtures.exception_group_with_nested_group)

    bugsnag_server.wait_for_event()
    assert bugsnag_server.sent_report_count == 1

    payload = bugsnag_server.events_received[0]['json_body']
    exceptions = payload['events'][0]['exceptions']

    # there should be 1 ExceptionGroup with 3 sub-exceptions
    assert len(exceptions) == 4

    assert exceptions[0] == {
        'message': 'the message of the group (3 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_nested_group',
                'lineNumber': 45,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': '<module>',
                'lineNumber': 49,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[1] == {
        'message': 'exception #1',
        'errorClass': 'Exception',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'generate_exception',
                'lineNumber': 15,
                'inProject': True,
                'code': None,
            }
        ]
    }

    assert exceptions[2] == {
        'message': 'the message of the group (4 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_no_cause',
                'lineNumber': 21,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': '<module>',
                'lineNumber': 25,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[3] == {
        'message': 'exception #3',
        'errorClass': 'ArithmeticError',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'generate_exception',
                'lineNumber': 15,
                'inProject': True,
                'code': None,
            }
        ]
    }


@pytest.mark.skipif(
    not is_exception_group_supported,
    reason="requires python 3.11 or the exceptiongroup pacakge"
)
def test_exception_group_implicit_cause_is_traversed(bugsnag_server):
    # disable send_code so we can assert against stacktraces more easily
    bugsnag.configure(send_code=False)

    bugsnag.notify(fixtures.exception_group_with_implicit_cause)

    bugsnag_server.wait_for_event()
    assert bugsnag_server.sent_report_count == 1

    payload = bugsnag_server.events_received[0]['json_body']
    exceptions = payload['events'][0]['exceptions']

    print(exceptions)

    # there should be 1 ExceptionGroup with 1 cause and 2 sub-exceptions
    assert len(exceptions) == 4

    # the ExceptionGroup
    assert exceptions[0] == {
        'message': 'group with implicit cause (2 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_implicit_cause',
                'lineNumber': 58,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': '<module>',
                'lineNumber': 62,
                'inProject': True,
                'code': None,
            },
        ],
    }

    # the cause - another ExceptionGroup
    # note: we don't recurse into this!
    assert exceptions[1] == {
        'message': 'the message of the group (3 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_nested_group',
                'lineNumber': 45,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_implicit_cause',
                'lineNumber': 56,
                'inProject': True,
                'code': None,
            },
        ],
    }

    # the exceptions in the original ExceptionGroup
    assert exceptions[2] == {
        'message': 'a',
        'errorClass': 'NameError',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/caused_by.py',
                'method': 'raise_exception_with_explicit_cause',
                'lineNumber': 5,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/caused_by.py',
                'method': '<module>',
                'lineNumber': 20,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[3] == {
        'message': 'exception #2',
        'errorClass': 'NameError',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'generate_exception',
                'lineNumber': 15,
                'inProject': True,
                'code': None,
            },
        ],
    }


@pytest.mark.skipif(
    not is_exception_group_supported,
    reason="requires python 3.11 or the exceptiongroup pacakge"
)
def test_exception_group_explicit_cause_is_traversed(bugsnag_server):
    # disable send_code so we can assert against stacktraces more easily
    bugsnag.configure(send_code=False)

    bugsnag.notify(fixtures.exception_group_with_explicit_cause)

    bugsnag_server.wait_for_event()
    assert bugsnag_server.sent_report_count == 1

    payload = bugsnag_server.events_received[0]['json_body']
    exceptions = payload['events'][0]['exceptions']

    print(exceptions)

    # 1 ExceptionGroup + 1 cause + 1 sub-cause + 2 sub-exceptions
    assert len(exceptions) == 5

    assert exceptions[0] == {
        'message': 'group with explicit cause (2 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_explicit_cause',
                'lineNumber': 71,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': '<module>',
                'lineNumber': 75,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[1] == {
        'message': 'group with implicit cause (2 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_implicit_cause',
                'lineNumber': 58,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_explicit_cause',
                'lineNumber': 69,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[2] == {
        'message': 'the message of the group (3 sub-exceptions)',
        'errorClass': expected_exception_group_class,
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_nested_group',
                'lineNumber': 45,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'raise_exception_group_with_implicit_cause',
                'lineNumber': 56,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[3] == {
        'message': 'exception #1',
        'errorClass': 'NameError',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/exception_groups.py',
                'method': 'generate_exception',
                'lineNumber': 15,
                'inProject': True,
                'code': None,
            },
        ],
    }

    assert exceptions[4] == {
        'message': 'a',
        'errorClass': 'NameError',
        'type': 'python',
        'stacktrace': [
            {
                'file': 'tests/fixtures/caused_by.py',
                'method': 'raise_exception_with_explicit_cause',
                'lineNumber': 5,
                'inProject': True,
                'code': None,
            },
            {
                'file': 'tests/fixtures/caused_by.py',
                'method': '<module>',
                'lineNumber': 20,
                'inProject': True,
                'code': None,
            },
        ],
    }
