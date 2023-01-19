from enum import Enum, unique
from typing import Any, Dict, List, Optional, Union, Callable, TYPE_CHECKING  # noqa
from collections import deque

from bugsnag.utils import FilterDict

# Deque is not present in 'typing' until 3.5.4, so we can't use it directly
if TYPE_CHECKING:
    from typing import Deque  # noqa

# The _breadcrumbs context var contains None or a deque of Breadcrumb instances
try:
    from contextvars import ContextVar
    _breadcrumbs = ContextVar(
        'bugsnag-breadcrumbs',
        default=None
    )  # type: ContextVar[Optional[Deque[Breadcrumb]]]
except ImportError:
    from bugsnag.utils import ThreadContextVar
    _breadcrumbs = ThreadContextVar('bugsnag-breadcrumbs', default=None)  # type: ignore  # noqa: E501


__all__ = (
    'BreadcrumbType',
    'Breadcrumb',
    'Breadcrumbs',
    'OnBreadcrumbCallback'
)


@unique
class BreadcrumbType(Enum):
    NAVIGATION = 'navigation'
    REQUEST = 'request'
    PROCESS = 'process'
    LOG = 'log'
    USER = 'user'
    STATE = 'state'
    ERROR = 'error'
    MANUAL = 'manual'


class Breadcrumb:
    def __init__(
        self,
        message: str,
        type: BreadcrumbType,
        metadata: Dict[str, Any],
        timestamp: str
    ):
        self.message = message
        self.type = type
        self.metadata = metadata
        self._timestamp = timestamp

    @property
    def timestamp(self) -> str:
        return self._timestamp

    # Convert this breadcrumb into a dict for use when JSON encoding
    def to_dict(self) -> Dict[str, Union[str, FilterDict]]:
        return {
            'timestamp': self._timestamp,
            'name': self.message,
            'type': self.type.value,
            'metaData': FilterDict(self.metadata)
        }


class Breadcrumbs:
    def __init__(self, max_breadcrumbs: int):
        self._max_breadcrumbs = max_breadcrumbs

        # Calling resize is important for tests as we make many Breadcrumbs
        # instances but they all have to share a ContextVar, so the size can
        # leak between tests
        self.resize(max_breadcrumbs)

    def append(self, breadcrumb: Breadcrumb) -> None:
        self._breadcrumbs.append(breadcrumb)

    # Resize the list of breadcrumbs if configuration.max_breadcrumbs changes
    def resize(self, new_max: int) -> None:
        old_breadcrumbs = self._breadcrumbs
        new_breadcrumbs = deque(old_breadcrumbs, maxlen=new_max)

        _breadcrumbs.set(new_breadcrumbs)
        self._max_breadcrumbs = new_max

    # Create a copy of the current list of breadcrumbs for this context
    def create_copy_for_context(self) -> None:
        # Resizing will create a new deque and store it in the ContextVar,
        # which will give the current context a new copy of the list
        self.resize(self._max_breadcrumbs)

    def clear(self) -> None:
        self._breadcrumbs.clear()

    def to_list(self) -> List[Breadcrumb]:
        return list(self._breadcrumbs)

    @property
    def _breadcrumbs(self):
        # type: () -> Deque[Breadcrumb]
        try:
            breadcrumbs = _breadcrumbs.get()
        except LookupError:
            breadcrumbs = None

        if breadcrumbs is None:
            breadcrumbs = deque(maxlen=self._max_breadcrumbs)
            _breadcrumbs.set(breadcrumbs)

        return breadcrumbs


OnBreadcrumbCallback = Callable[[Breadcrumb], Union[None, bool]]
