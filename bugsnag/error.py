from typing import Any, Dict, List

__all__ = ('Error',)


class Error:
    __slots__ = (
        'error_class',
        'error_message',
        'stacktrace',
        'type',
    )

    def __init__(
        self,
        error_class: str,
        error_message: str,
        stacktrace: List[Dict[str, Any]]
    ):
        self.error_class = error_class
        self.error_message = error_message
        self.stacktrace = stacktrace
        self.type = 'python'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'errorClass': self.error_class,
            'message': self.error_message,
            'stacktrace': self.stacktrace,
            'type': self.type,
        }
