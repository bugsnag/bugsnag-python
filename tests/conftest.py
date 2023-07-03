import pytest
import bugsnag
import bugsnag.legacy as global_setup
from tests.utils import FakeBugsnagServer


# resize the breadcrumb list to 0 before each test to prevent tests from
# interfering with eachother
@pytest.fixture(autouse=True)
def reset_breadcrumbs():
    bugsnag.Breadcrumbs(0).resize(0)


@pytest.fixture
def bugsnag_server():
    server = FakeBugsnagServer(wait_for_duplicate_requests=False)
    bugsnag.configure(endpoint=server.url, api_key='3874876376238728937')

    yield server

    # Reset shared client config
    global_setup.configuration = bugsnag.Configuration()
    global_setup.default_client.configuration = global_setup.configuration
    global_setup.default_client.uninstall_sys_hook()

    server.shutdown()
