import bugsnag
from bugsnag import legacy


def test_legacy_configuration_sync():
    """After calling `bugsnag.configure(...)`, the package and legacy
    configuration objects should point to the same live objects.
    This prevents an import-time snapshot from becoming stale.
    """
    bugsnag.configure(api_key="test-api-key")

    assert bugsnag.configuration is legacy.configuration
    assert getattr(bugsnag, "logger", None) is getattr(legacy, "logger", None)
