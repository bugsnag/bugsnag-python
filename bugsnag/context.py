from weakref import WeakKeyDictionary
from bugsnag.feature_flags import FeatureFlagDelegate


try:
    from contextvars import ContextVar  # type: ignore
except ImportError:
    from bugsnag.utils import ThreadContextVar as ContextVar  # type: ignore  # noqa: E501


# a top-level context var storing a WeakKeyDictionary of client => state
# the WeakKeyDictionary ensures that when a client object is garbage collected
# its state is discarded as well
_client_contexts = ContextVar('bugsnag-client-context', default=None)


def _raw_get(client, key):
    client_context = _client_contexts.get()

    if (
        client_context is not None and
        client in client_context and
        key in client_context[client]
    ):
        return client_context[client][key]

    return None


def _raw_set(client, key, value):
    client_context = _client_contexts.get()

    if client_context is None:
        client_context = WeakKeyDictionary()
        _client_contexts.set(client_context)

    if client not in client_context:
        client_context[client] = {}

    client_context[client][key] = value


def create_new_context():
    _client_contexts.set(None)


FEATURE_FLAG_DELEGATE_KEY = 'feature_flag_delegate'


class ContextLocalState:
    def __init__(self, client):
        self._client = client

    @property
    def feature_flag_delegate(self) -> FeatureFlagDelegate:
        delegate = _raw_get(self._client, FEATURE_FLAG_DELEGATE_KEY)

        # create a new delegate if one does not exist already
        if delegate is None:
            delegate = FeatureFlagDelegate()
            _raw_set(self._client, FEATURE_FLAG_DELEGATE_KEY, delegate)

        return delegate
