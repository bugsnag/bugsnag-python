import pytest
from tests.utils import FakeBugsnagServer

import bugsnag


@pytest.fixture
def bugsnag_server():
    server = FakeBugsnagServer()
    bugsnag.configure(endpoint=server.url, api_key='3874876376238728937')

    yield server

    bugsnag.configure(app_type=None)
    server.shutdown()
