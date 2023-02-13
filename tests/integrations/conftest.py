import pytest
import bugsnag
import bugsnag.legacy as global_setup
from tests.utils import FakeBugsnagServer


@pytest.fixture
def bugsnag_server():
    server = FakeBugsnagServer(wait_for_duplicate_requests=True)
    bugsnag.configure(endpoint=server.url, api_key='3874876376238728937')

    yield server

    # Reset shared client config
    global_setup.configuration = bugsnag.Configuration()
    global_setup.default_client.configuration = global_setup.configuration
    global_setup.default_client.uninstall_sys_hook()

    server.shutdown()
