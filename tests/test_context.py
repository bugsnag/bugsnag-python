import sys
import pytest
import asyncio
from time import sleep
from threading import Thread
from random import shuffle, randrange
from bugsnag.client import Client
from bugsnag.feature_flags import FeatureFlag
from bugsnag.context import create_new_context


def test_state_is_stored_separately_per_thread():
    client1 = Client()
    client2 = Client()

    assert client1.feature_flags == []
    assert client2.feature_flags == []

    client1.add_feature_flag('a')
    client2.add_feature_flag('b')

    assert client1.feature_flags == [FeatureFlag('a')]
    assert client2.feature_flags == [FeatureFlag('b')]

    def thread_target(client1, client2, id):
        thread.exception = None

        try:
            # sleep for a bit to allow other threads time to interfere
            sleep(randrange(0, 100) / 1000)

            assert client1.feature_flags == []
            assert client2.feature_flags == []

            client1.add_feature_flag('client1 (#%d) 1' % id)
            client2.add_feature_flag('client2 (#%d) 1' % id)

            # sleep for a bit to allow other threads time to interfere
            sleep(randrange(0, 100) / 1000)

            client1.add_feature_flag('client1 (#%d) 2' % id)
            client2.add_feature_flag('client2 (#%d) 2' % id)

            assert client1.feature_flags == [
                FeatureFlag('client1 (#%d) 1' % id),
                FeatureFlag('client1 (#%d) 2' % id)
            ]

            assert client2.feature_flags == [
                FeatureFlag('client2 (#%d) 1' % id),
                FeatureFlag('client2 (#%d) 2' % id)
            ]

        except Exception as e:
            thread.exception = e

    threads = []

    for i in range(10):
        thread = Thread(target=thread_target, args=(client1, client2, i))
        threads.append(thread)

    shuffle(threads)

    for thread in threads:
        thread.start()

    shuffle(threads)

    for thread in threads:
        thread.join(2)

        assert not thread.is_alive()

        if thread.exception is not None:
            raise thread.exception

    # changes in other threads should not affect this thread
    assert client1.feature_flags == [FeatureFlag('a')]
    assert client2.feature_flags == [FeatureFlag('b')]


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="requires ContextVar support (Python 3.7 or higher)"
)
def test_state_is_stored_separately_per_async_context():
    client1 = Client()
    client2 = Client()

    assert client1.feature_flags == []
    assert client2.feature_flags == []

    client1.add_feature_flag('a')
    client2.add_feature_flag('b')

    assert client1.feature_flags == [FeatureFlag('a')]
    assert client2.feature_flags == [FeatureFlag('b')]

    async def mutate_state(id):
        create_new_context()

        await asyncio.sleep(randrange(0, 100) / 1000)

        assert client1.feature_flags == []
        assert client2.feature_flags == []

        client1.add_feature_flag('client1 (#%d) 1' % id)
        await asyncio.sleep(randrange(0, 100) / 1000)

        client2.add_feature_flag('client2 (#%d) 1' % id)
        await asyncio.sleep(randrange(0, 100) / 1000)

        assert client1.feature_flags == [FeatureFlag('client1 (#%d) 1' % id)]
        assert client2.feature_flags == [FeatureFlag('client2 (#%d) 1' % id)]

        client1.add_feature_flag('client1 (#%d) 2' % id)
        client2.add_feature_flag('client2 (#%d) 2' % id)

        await asyncio.sleep(randrange(0, 100) / 1000)

        assert client1.feature_flags == [
            FeatureFlag('client1 (#%d) 1' % id),
            FeatureFlag('client1 (#%d) 2' % id),
        ]

        assert client2.feature_flags == [
            FeatureFlag('client2 (#%d) 1' % id),
            FeatureFlag('client2 (#%d) 2' % id),
        ]

    async def test():
        tasks = [mutate_state(i) for i in range(10)]

        await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(test())
    finally:
        loop.close()

    assert client1.feature_flags == [FeatureFlag('a')]
    assert client2.feature_flags == [FeatureFlag('b')]
