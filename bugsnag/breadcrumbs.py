from enum import Enum, unique
from typing import Any, Dict, Union
from bugsnag.utils import FilterDict


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
