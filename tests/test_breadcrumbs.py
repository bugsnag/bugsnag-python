from bugsnag import BreadcrumbType


def test_breadcrumb_types():
    assert len(BreadcrumbType) == 8

    assert BreadcrumbType.NAVIGATION.value == 'navigation'
    assert BreadcrumbType.REQUEST.value == 'request'
    assert BreadcrumbType.PROCESS.value == 'process'
    assert BreadcrumbType.LOG.value == 'log'
    assert BreadcrumbType.USER.value == 'user'
    assert BreadcrumbType.STATE.value == 'state'
    assert BreadcrumbType.ERROR.value == 'error'
    assert BreadcrumbType.MANUAL.value == 'manual'
