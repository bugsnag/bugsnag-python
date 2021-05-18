from bugsnag import BreadcrumbType, Breadcrumb
from bugsnag.utils import FilterDict


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


def test_breadcrumb_properties():
    breadcrumb = Breadcrumb(
        'This is a test breadcrumb',
        BreadcrumbType.REQUEST,
        {'a': 1, 'b': 2, 'c': 3, 'xyz': 456},
        '1234-56-78T12:34:56.789+00:00'
    )

    assert breadcrumb.message == 'This is a test breadcrumb'
    assert breadcrumb.type == BreadcrumbType.REQUEST
    assert breadcrumb.metadata == {'a': 1, 'b': 2, 'c': 3, 'xyz': 456}
    assert breadcrumb.timestamp == '1234-56-78T12:34:56.789+00:00'


def test_breadcrumb_properties_with_keyword_params():
    breadcrumb = Breadcrumb(
        timestamp='9876-54-32T12:34:56.789+00:00',
        metadata={'a': 1, 'b': 2, 'c': 3, 'xyz': 456},
        type=BreadcrumbType.PROCESS,
        message='This is a second test breadcrumb'
    )

    assert breadcrumb.message == 'This is a second test breadcrumb'
    assert breadcrumb.type == BreadcrumbType.PROCESS
    assert breadcrumb.metadata == {'a': 1, 'b': 2, 'c': 3, 'xyz': 456}
    assert breadcrumb.timestamp == '9876-54-32T12:34:56.789+00:00'


def test_breadcrumb_to_dict():
    breadcrumb = Breadcrumb(
        'This is another test breadcrumb',
        BreadcrumbType.ERROR,
        {'abc': 123, 'xyz': 'fourfivesix'},
        '1234-56-78T12:34:56.789+00:00'
    )

    breadcrumb_dict = breadcrumb.to_dict()

    expected = {
        'name': 'This is another test breadcrumb',
        'type': BreadcrumbType.ERROR.value,
        'metaData': FilterDict({'abc': 123, 'xyz': 'fourfivesix'}),
        'timestamp': '1234-56-78T12:34:56.789+00:00'
    }

    assert breadcrumb_dict == expected

    # pytest allows the previous assertion to pass when metadata is not a
    # FilterDict, so explicitly check for this as it's necessary for redaction
    assert isinstance(breadcrumb_dict['metaData'], FilterDict)
