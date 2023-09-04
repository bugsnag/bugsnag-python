from collections import OrderedDict
from typing import Dict, List, Union


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
            return {'featureFlag': self._name}

        return {'featureFlag': self._name, 'variant': self._variant}

    # a FeatureFlag is valid if it has a non-empty string name and a variant
    # that's None or a string
    # FeatureFlags that are not valid will be ignored
    def is_valid(self) -> bool:
        return (
            isinstance(self._name, (str, bytes)) and
            len(self._name) > 0 and
            (self._variant is None or isinstance(self._variant, (str, bytes)))
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, FeatureFlag):
            return (
                self._name == other._name and
                self._variant == other._variant
            )

        return NotImplemented

    def __hash__(self):
        return hash((self._name, self._variant))

    def __repr__(self):
        return 'FeatureFlag(%s, %s)' % (repr(self._name), repr(self._variant))

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


class FeatureFlagDelegate:
    def __init__(self):
        self._storage = OrderedDict()

    def add(
        self,
        name: Union[str, bytes],
        variant: Union[None, str, bytes]
    ) -> None:
        flag = FeatureFlag(name, variant)

        if flag.is_valid():
            self._storage[flag.name] = flag

    def merge(self, flags: List[FeatureFlag]) -> None:
        for flag in flags:
            if isinstance(flag, FeatureFlag) and flag.is_valid():
                self._storage[flag.name] = flag

    def remove(self, name: Union[str, bytes]) -> None:
        if name in self._storage:
            del self._storage[name]

    def clear(self) -> None:
        self._storage.clear()

    def copy(self) -> 'FeatureFlagDelegate':
        copy = FeatureFlagDelegate()
        copy._storage = self._storage.copy()

        return copy

    def to_list(self) -> List[FeatureFlag]:
        return list(self._storage.values())

    def to_json(self) -> List[Dict[str, Union[str, bytes]]]:
        return [flag.to_dict() for flag in self.to_list()]
