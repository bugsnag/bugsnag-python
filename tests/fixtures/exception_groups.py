# flake8: noqa
try:
    from exceptiongroup import ExceptionGroup, BaseExceptionGroup # noqa
except ImportError:
    # if we're here and 'exceptiongroup' isn't installed, it must mean we're on
    # Python 3.11+ and have support natively
    pass

from .caused_by import exception_with_explicit_cause

# this creates an exception with a very small __traceback__, so it's easier to
# assert against in tests
def generate_exception(exception_class, message):
    try:
        raise exception_class(message)
    except BaseException as exception:
        return exception


def raise_exception_group_with_no_cause():
    raise ExceptionGroup('the message of the group', [generate_exception(Exception, 'exception #1'), generate_exception(ArithmeticError, 'exception #2'), generate_exception(NameError, 'exception #3'), generate_exception(AssertionError, 'exception #4')])


try:
    raise_exception_group_with_no_cause()
except BaseExceptionGroup as exception_group:
    exception_group_with_no_cause = exception_group


class MyExceptionGroup(BaseExceptionGroup):
    pass


def raise_base_exception_group_subclass_with_no_cause():
    raise MyExceptionGroup('my very easy method just speeds up (n)making exception groups', [generate_exception(GeneratorExit, 'exception #1'), generate_exception(ReferenceError, 'exception #2'), generate_exception(NotImplementedError, 'exception #3')])


try:
    raise_base_exception_group_subclass_with_no_cause()
except BaseExceptionGroup as exception_group:
    base_exception_group_subclass = exception_group


def raise_exception_group_with_nested_group():
    raise ExceptionGroup('the message of the group', [generate_exception(Exception, 'exception #1'), exception_group_with_no_cause, generate_exception(ArithmeticError, 'exception #3')])


try:
    raise_exception_group_with_nested_group()
except BaseExceptionGroup as exception_group:
    exception_group_with_nested_group = exception_group


def raise_exception_group_with_implicit_cause():
    try:
        raise_exception_group_with_nested_group()
    except BaseExceptionGroup as exception_group:
        raise ExceptionGroup('group with implicit cause', [exception_with_explicit_cause, generate_exception(NameError, 'exception #2')])


try:
    raise_exception_group_with_implicit_cause()
except BaseExceptionGroup as exception_group:
    exception_group_with_implicit_cause = exception_group


def raise_exception_group_with_explicit_cause():
    try:
        raise_exception_group_with_implicit_cause()
    except BaseExceptionGroup as exception_group:
        raise ExceptionGroup('group with explicit cause', [generate_exception(NameError, 'exception #1'), exception_with_explicit_cause]) from exception_group


try:
    raise_exception_group_with_explicit_cause()
except BaseExceptionGroup as exception_group:
    exception_group_with_explicit_cause = exception_group
