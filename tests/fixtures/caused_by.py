def a():
    try:
        b()
    except Exception as cause:
        raise NameError('a') from cause


def b():
    try:
        c()
    except Exception as cause:
        raise ArithmeticError('b') from cause


def c():
    raise Exception('c')


try:
    a()
except Exception as exception:
    exception_with_explicit_cause = exception


def x():
    try:
        y()
    except Exception:
        raise NameError('x')


def y():
    try:
        z()
    except Exception:
        raise ArithmeticError('y')


def z():
    raise Exception('z')


try:
    x()
except Exception as exception:
    exception_with_implicit_cause = exception


def one():
    try:
        two()
    except Exception:
        raise NameError('one') from None


def two():
    try:
        three()
    except Exception:
        raise ArithmeticError('two')


def three():
    raise Exception('three')


try:
    one()
except Exception as exception:
    exception_with_no_cause = exception
