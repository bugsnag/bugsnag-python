import asyncio
import random
import time
import sys
import pytest
from threading import Thread

from bugsnag import BreadcrumbType, Breadcrumb, Breadcrumbs
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


def test_there_is_a_max_number_of_breadcrumbs():
    breadcrumbs = Breadcrumbs(max_breadcrumbs=2)

    first_breadcrumb = Breadcrumb('hello', BreadcrumbType.ERROR, {}, 'time')
    second_breadcrumb = Breadcrumb('hi', BreadcrumbType.REQUEST, {}, 'emit')

    breadcrumbs.append(first_breadcrumb)
    breadcrumbs.append(second_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 2
    assert breadcrumb_list[0] == first_breadcrumb
    assert breadcrumb_list[1] == second_breadcrumb

    third_breadcrumb = Breadcrumb('howdy', BreadcrumbType.LOG, {}, 'now')
    breadcrumbs.append(third_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    # the length should match the maximum number of breadcrumbs set earlier
    assert len(breadcrumb_list) == 2
    assert breadcrumb_list[0] == second_breadcrumb
    assert breadcrumb_list[1] == third_breadcrumb


def test_the_number_of_breadcrumbs_can_be_reduced():
    breadcrumbs = Breadcrumbs(max_breadcrumbs=3)

    first_breadcrumb = Breadcrumb('hello', BreadcrumbType.ERROR, {}, 'time')
    second_breadcrumb = Breadcrumb('hi', BreadcrumbType.REQUEST, {}, 'emit')
    third_breadcrumb = Breadcrumb('howdy', BreadcrumbType.LOG, {}, 'now')

    breadcrumbs.append(first_breadcrumb)
    breadcrumbs.append(second_breadcrumb)
    breadcrumbs.append(third_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 3
    assert breadcrumb_list[0] == first_breadcrumb
    assert breadcrumb_list[1] == second_breadcrumb
    assert breadcrumb_list[2] == third_breadcrumb

    breadcrumbs.resize(1)
    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 1
    assert breadcrumb_list[0] == third_breadcrumb

    breadcrumbs.resize(0)
    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 0


def test_the_number_of_breadcrumbs_can_be_increased():
    breadcrumbs = Breadcrumbs(max_breadcrumbs=1)

    first_breadcrumb = Breadcrumb('hello', BreadcrumbType.ERROR, {}, 'time')

    breadcrumbs.append(first_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 1
    assert breadcrumb_list[0] == first_breadcrumb

    second_breadcrumb = Breadcrumb('hi', BreadcrumbType.REQUEST, {}, 'emit')
    third_breadcrumb = Breadcrumb('howdy', BreadcrumbType.LOG, {}, 'now')

    breadcrumbs.resize(5)

    breadcrumbs.append(second_breadcrumb)
    breadcrumbs.append(third_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 3
    assert breadcrumb_list[0] == first_breadcrumb
    assert breadcrumb_list[1] == second_breadcrumb
    assert breadcrumb_list[2] == third_breadcrumb

    breadcrumbs.append(second_breadcrumb)
    breadcrumbs.append(third_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 5
    assert breadcrumb_list[0] == first_breadcrumb
    assert breadcrumb_list[1] == second_breadcrumb
    assert breadcrumb_list[2] == third_breadcrumb
    assert breadcrumb_list[3] == second_breadcrumb
    assert breadcrumb_list[4] == third_breadcrumb


def test_the_breadcrumb_list_is_separate_on_different_threads():
    breadcrumbs = Breadcrumbs(max_breadcrumbs=5)

    def append_breadcrumbs(id):
        try:
            thread.exception = None

            first_breadcrumb = Breadcrumb(
                'a' + id,
                BreadcrumbType.ERROR,
                {'a': id, 'b': 'xyz'},
                'x'
            )

            second_breadcrumb = Breadcrumb(
                'b' + id,
                BreadcrumbType.USER,
                {'b': id, 'c': 'xyz'},
                'y'
            )

            third_breadcrumb = Breadcrumb(
                'c' + id,
                BreadcrumbType.STATE,
                {'c': id, 'xyz': 'yes'},
                'z'
            )

            breadcrumbs.append(first_breadcrumb)
            breadcrumbs.append(second_breadcrumb)
            breadcrumbs.append(third_breadcrumb)

            # sleep for a bit to allow other threads time to interfere
            time.sleep(random.randrange(0, 100) / 1000)

            breadcrumb_list = breadcrumbs.to_list()

            assert len(breadcrumb_list) == 3
            assert breadcrumb_list[0] == first_breadcrumb
            assert breadcrumb_list[1] == second_breadcrumb
            assert breadcrumb_list[2] == third_breadcrumb

            breadcrumbs.append(second_breadcrumb)
            breadcrumbs.append(third_breadcrumb)

            # sleep for a bit to allow other threads time to interfere
            time.sleep(random.randrange(0, 100) / 1000)

            breadcrumb_list = breadcrumbs.to_list()

            assert len(breadcrumb_list) == 5
            assert breadcrumb_list[0] == first_breadcrumb
            assert breadcrumb_list[1] == second_breadcrumb
            assert breadcrumb_list[2] == third_breadcrumb
            assert breadcrumb_list[3] == second_breadcrumb
            assert breadcrumb_list[4] == third_breadcrumb

            breadcrumbs.resize(2)

            # sleep for a bit to allow other threads time to interfere
            time.sleep(random.randrange(0, 100) / 1000)

            breadcrumb_list = breadcrumbs.to_list()

            assert len(breadcrumb_list) == 2
            assert breadcrumb_list[0] == second_breadcrumb
            assert breadcrumb_list[1] == third_breadcrumb

        except Exception as e:
            thread.exception = e

    threads = []
    for i in range(5):
        thread = Thread(target=append_breadcrumbs, args=[str(i)])
        threads.append(thread)

    # shuffle the list of threads so they don't run in a reliable order
    random.shuffle(threads)

    for thread in threads:
        thread.start()

    # shuffle the list of threads so they don't run in a reliable order
    random.shuffle(threads)

    for thread in threads:
        thread.join(2)

        assert not thread.is_alive()

        # if an exception happened in the thread, raise it here instead
        if thread.exception is not None:
            raise thread.exception


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="requires ContextVar support (Python 3.7 or higher)"
)
def test_the_breadcrumb_list_is_separate_on_different_async_contexts():
    breadcrumbs = Breadcrumbs(max_breadcrumbs=5)

    async def append_breadcrumbs(id):
        # create a copy of the breadcrumbs for this context
        breadcrumbs.create_copy_for_context()

        first_breadcrumb = Breadcrumb(
            'a' + id,
            BreadcrumbType.ERROR,
            {'a': id, 'b': 'xyz'},
            'x'
        )

        second_breadcrumb = Breadcrumb(
            'b' + id,
            BreadcrumbType.USER,
            {'b': id, 'c': 'xyz'},
            'y'
        )

        third_breadcrumb = Breadcrumb(
            'c' + id,
            BreadcrumbType.STATE,
            {'c': id, 'xyz': 'yes'},
            'z'
        )

        breadcrumbs.append(first_breadcrumb)
        breadcrumbs.append(second_breadcrumb)
        breadcrumbs.append(third_breadcrumb)

        await asyncio.sleep(random.randrange(0, 100) / 1000)

        breadcrumb_list = breadcrumbs.to_list()

        assert len(breadcrumb_list) == 3
        assert breadcrumb_list[0] == first_breadcrumb
        assert breadcrumb_list[1] == second_breadcrumb
        assert breadcrumb_list[2] == third_breadcrumb

        breadcrumbs.append(second_breadcrumb)
        breadcrumbs.append(third_breadcrumb)

        await asyncio.sleep(random.randrange(0, 100) / 1000)

        breadcrumb_list = breadcrumbs.to_list()

        assert len(breadcrumb_list) == 5
        assert breadcrumb_list[0] == first_breadcrumb
        assert breadcrumb_list[1] == second_breadcrumb
        assert breadcrumb_list[2] == third_breadcrumb
        assert breadcrumb_list[3] == second_breadcrumb
        assert breadcrumb_list[4] == third_breadcrumb

        breadcrumbs.resize(2)

        await asyncio.sleep(random.randrange(0, 100) / 1000)

        breadcrumb_list = breadcrumbs.to_list()

        assert len(breadcrumb_list) == 2
        assert breadcrumb_list[0] == second_breadcrumb
        assert breadcrumb_list[1] == third_breadcrumb

    async def test():
        tasks = []
        for i in range(5):
            tasks.append(asyncio.ensure_future(append_breadcrumbs(str(i))))

        await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(test())
    finally:
        loop.close()


def test_the_breadcrumb_list_can_be_cleared():
    breadcrumbs = Breadcrumbs(max_breadcrumbs=5)

    first_breadcrumb = Breadcrumb('hello', BreadcrumbType.ERROR, {}, 'time')
    second_breadcrumb = Breadcrumb('hi', BreadcrumbType.REQUEST, {}, 'emit')
    third_breadcrumb = Breadcrumb('howdy', BreadcrumbType.LOG, {}, 'now')

    breadcrumbs.append(first_breadcrumb)
    breadcrumbs.append(second_breadcrumb)
    breadcrumbs.append(third_breadcrumb)

    breadcrumb_list = breadcrumbs.to_list()

    assert len(breadcrumb_list) == 3
    assert breadcrumb_list[0] == first_breadcrumb
    assert breadcrumb_list[1] == second_breadcrumb
    assert breadcrumb_list[2] == third_breadcrumb

    breadcrumbs.clear()

    assert len(breadcrumbs.to_list()) == 0
