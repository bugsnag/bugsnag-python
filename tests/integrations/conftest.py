import pytest
from tests.utils import FakeBugsnagServer

import bugsnag


@pytest.fixture
def bugsnag_server():
    server = FakeBugsnagServer()
    bugsnag.configure(endpoint=server.url, api_key='3874876376238728937')

    yield server

    # Reset shared client config
    bugsnag.default_client.uninstall_sys_hook()
    bugsnag.default_client.configuration = bugsnag.Configuration()
    bugsnag.configuration = bugsnag.default_client.configuration

    server.shutdown()
