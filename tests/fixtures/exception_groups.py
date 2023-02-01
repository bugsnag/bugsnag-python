# flake8: noqa

# this creates an exception with a very small __traceback__, so it's easier to
# assert against in tests
def generate_exception(exception_class, message):
    try:
        raise exception_class(message)
    except Exception as exception:
        return exception


def raise_exception_group_with_no_cause():
    raise ExceptionGroup(
        'the message of the group',
        [
            generate_exception(Exception, 'exception #1'),
            generate_exception(ArithmeticError, 'exception #2'),
            generate_exception(NameError, 'exception #3'),
            generate_exception(AssertionError, 'exception #4'),
        ]
    )


try:
    raise_exception_group_with_no_cause()
except BaseExceptionGroup as exception_group:
    exception_group_with_no_cause = exception_group
