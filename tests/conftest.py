import pytest
from bugsnag import Breadcrumbs


# resize the breadcrumb list to 0 before each test to prevent tests from
# interfering with eachother
@pytest.fixture(autouse=True)
def reset_breadcrumbs():
    Breadcrumbs(0).resize(0)
