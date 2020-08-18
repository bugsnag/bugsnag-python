import pytest
from tests.utils import FakeBugsnagServer

import bugsnag.legacy as global_setup
import bugsnag


@pytest.fixture
def bugsnag_server():
    server = FakeBugsnagServer()
    bugsnag.configure(endpoint=server.url, api_key='3874876376238728937')

    yield server

    # Reset shared client config
    global_setup.configuration = bugsnag.Configuration()
    global_setup.default_client.configuration = global_setup.configuration

    server.shutdown()
