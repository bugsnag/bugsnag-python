import pytest
from tests.utils import FakeBugsnagServer

import bugsnag


@pytest.fixture
def bugsnag_server():
    server = FakeBugsnagServer()
    bugsnag.configure(endpoint=server.url, api_key='3874876376238728937')

    yield server

    server.shutdown()


@pytest.fixture
def asgi_wrapper():
    from tests.async_utils import ASGITestClient
    yield ASGITestClient


@pytest.fixture
def async_bugsnag_server():
    from tests.async_utils import FakeBugsnag
    server = FakeBugsnag()
    bugsnag.configure(endpoint=server.events_url,
                      session_endpoint=server.sessions_url,
                      api_key='3874876376238728937')

    yield server

    server.shutdown()
