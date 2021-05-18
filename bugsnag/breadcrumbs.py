from enum import Enum, unique


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
