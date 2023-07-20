from typing import Dict, Union


class FeatureFlag:
    def __init__(
        self,
        name: Union[str, bytes],
        variant: Union[None, str, bytes] = None
    ):
        self._name = name
        self._variant = self._coerce_variant(variant)

    @property
    def name(self) -> Union[str, bytes]:
        return self._name

    @property
    def variant(self) -> Union[None, str, bytes]:
        return self._variant

    # for JSON encoding the feature flag
    def to_dict(self) -> Dict[str, Union[str, bytes]]:
        if self._variant is None:
            return {'name': self._name}

        return {'name': self._name, 'variant': self._variant}

    # a FeatureFlag is valid if it has a non-empty string name and a variant
    # that's None or a string
    # FeatureFlags that are not valid will be ignored
    def is_valid(self) -> bool:
        return (
            isinstance(self._name, (str, bytes)) and
            len(self._name) > 0 and
            (self._variant is None or isinstance(self._variant, (str, bytes)))
        )

    def _coerce_variant(
        self,
        variant: Union[None, str, bytes]
    ) -> Union[None, str, bytes]:
        if variant is None or isinstance(variant, (str, bytes)):
            return variant

        try:
            return str(variant)
        except Exception:
            return None
