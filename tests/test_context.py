import sys
import pytest
import asyncio
from time import sleep
from threading import Thread
from random import shuffle, randrange
from bugsnag.context import ContextLocalState


class Client:
    def __init__(self):
        self.state = ContextLocalState(self)


def test_state_is_stored_separately_per_thread():
    client1 = Client()
    client2 = Client()

    assert client1.state.feature_flag_delegate is None
    assert client2.state.feature_flag_delegate is None

    client1.state.feature_flag_delegate = 'a delegate'
    client2.state.feature_flag_delegate = 'another delegate'

    assert client1.state.feature_flag_delegate == 'a delegate'
    assert client2.state.feature_flag_delegate == 'another delegate'

    def thread_target(client1, client2, id):
        thread.exception = None

        try:
            # sleep for a bit to allow other threads time to interfere
            sleep(randrange(0, 100) / 1000)

            assert client1.state.feature_flag_delegate is None
            assert client2.state.feature_flag_delegate is None

            client1.state.feature_flag_delegate = 'client1 (#%d)' % id
            client2.state.feature_flag_delegate = 'client2 (#%d)' % id

            # sleep for a bit to allow other threads time to interfere
            sleep(randrange(0, 100) / 1000)

            assert client1.state.feature_flag_delegate == 'client1 (#%d)' % id
            assert client2.state.feature_flag_delegate == 'client2 (#%d)' % id
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
    assert client1.state.feature_flag_delegate == 'a delegate'
    assert client2.state.feature_flag_delegate == 'another delegate'


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="requires ContextVar support (Python 3.7 or higher)"
)
def test_state_is_stored_separately_per_async_context():
    client1 = Client()
    client2 = Client()

    assert client1.state.feature_flag_delegate is None
    assert client2.state.feature_flag_delegate is None

    async def mutate_state(id):
        client1.state.create_copy_for_context()
        client2.state.create_copy_for_context()

        client1.state.feature_flag_delegate = None
        client2.state.feature_flag_delegate = None

        await asyncio.sleep(randrange(0, 100) / 1000)

        assert client1.state.feature_flag_delegate is None
        assert client2.state.feature_flag_delegate is None

        client1.state.feature_flag_delegate = 'client1 (#%d)' % id
        await asyncio.sleep(randrange(0, 100) / 1000)

        client2.state.feature_flag_delegate = 'client2 (#%d)' % id
        await asyncio.sleep(randrange(0, 100) / 1000)

        assert client1.state.feature_flag_delegate == 'client1 (#%d)' % id
        assert client2.state.feature_flag_delegate == 'client2 (#%d)' % id

        client1.state.feature_flag_delegate = 'client1 (#%d) 2' % id
        client2.state.feature_flag_delegate = 'client2 (#%d) 2' % id

        await asyncio.sleep(randrange(0, 100) / 1000)

        assert client1.state.feature_flag_delegate == 'client1 (#%d) 2' % id
        assert client2.state.feature_flag_delegate == 'client2 (#%d) 2' % id

    async def test():
        tasks = []
        for i in range(10):
            tasks.append(mutate_state(i))

        await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(test())
    finally:
        loop.close()

    assert client1.state.feature_flag_delegate is None
    assert client2.state.feature_flag_delegate is None
