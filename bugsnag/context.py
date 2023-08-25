from weakref import WeakKeyDictionary


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


def _raw_copy(client):
    client_context = _client_contexts.get()

    # no need to copy if there is no existing value
    if client_context is None:
        return

    _client_contexts.set(client_context.copy())


FEATURE_FLAG_DELEGATE_KEY = 'feature_flag_delegate'


class ContextLocalState:
    def __init__(self, client):
        self._client = client

    def create_copy_for_context(self):
        _raw_copy(self._client)

    @property
    def feature_flag_delegate(self):
        return _raw_get(self._client, FEATURE_FLAG_DELEGATE_KEY)

    @feature_flag_delegate.setter
    def feature_flag_delegate(self, new_delegate):
        _raw_set(self._client, FEATURE_FLAG_DELEGATE_KEY, new_delegate)
