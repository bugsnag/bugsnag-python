from bugsnag.feature_flags import FeatureFlag


class Unstringable:
    def __str__(self):
        raise Exception('no')

    def __repr__(self):
        raise Exception('nope')


def test_feature_flag_has_name_and_variant():
    flag = FeatureFlag('abc', 'xyz')

    assert flag.name == 'abc'
    assert flag.variant == 'xyz'


def test_feature_flag_variant_is_optional():
    assert FeatureFlag('a').variant is None
    assert FeatureFlag('a', None).variant is None


def test_feature_flag_variant_is_coerced_to_string():
    assert FeatureFlag('a', 123).variant == '123'
    assert FeatureFlag('a', [1, 2, 3]).variant == '[1, 2, 3]'


def test_feature_flag_name_and_variant_can_be_bytes():
    flag = FeatureFlag(b'abc', b'xyz')

    assert flag.name == b'abc'
    assert flag.variant == b'xyz'


def test_feature_flag_variant_is_unset_if_not_coercable():
    assert FeatureFlag('a', Unstringable()).variant is None


def test_feature_flag_can_be_converted_to_dict():
    flag = FeatureFlag('abc', 'xyz')

    assert flag.to_dict() == {'name': 'abc', 'variant': 'xyz'}


def test_feature_flag_dict_does_not_have_variant_when_variant_is_not_given():
    flag = FeatureFlag('xyz')

    assert flag.to_dict() == {'name': 'xyz'}


def test_feature_flag_dict_does_not_have_variant_when_variant_is_none():
    flag = FeatureFlag('abc', variant=None)

    assert flag.to_dict() == {'name': 'abc'}


def test_a_feature_flag_with_name_and_variant_is_valid():
    assert FeatureFlag('abc', 'xyz').is_valid() is True
    assert FeatureFlag('abc', b'xyz').is_valid() is True
    assert FeatureFlag(b'abc', b'xyz').is_valid() is True
    assert FeatureFlag(b'abc', 'xyz').is_valid() is True


def test_a_feature_flag_with_only_name_is_valid():
    flag = FeatureFlag('b')

    assert flag.is_valid() is True


def test_a_feature_flag_with_empty_name_is_not_valid():
    flag = FeatureFlag('')

    assert flag.is_valid() is False


def test_a_feature_flag_with_none_name_is_not_valid():
    flag = FeatureFlag(None)

    assert flag.is_valid() is False
