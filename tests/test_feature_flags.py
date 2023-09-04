from bugsnag.feature_flags import FeatureFlag, FeatureFlagDelegate
import pytest


class Unstringable:
    def __str__(self):
        raise Exception('no')

    def __repr__(self):
        raise Exception('nope')


_invalid_names = [
    (None,),
    (True,),
    (False,),
    (1234,),
    ([1, 2, 3],),
    ({'a': 1, 'b': 2},),
    ('',)
]


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


def test_feature_flag_implements_repr():
    assert repr(FeatureFlag('abc', 'xyz')) == "FeatureFlag('abc', 'xyz')"
    assert repr(FeatureFlag('ayc', None)) == "FeatureFlag('ayc', None)"
    assert repr(FeatureFlag('xyz')) == "FeatureFlag('xyz', None)"


def test_feature_flag_can_be_converted_to_dict():
    flag = FeatureFlag('abc', 'xyz')

    assert flag.to_dict() == {'featureFlag': 'abc', 'variant': 'xyz'}


def test_feature_flag_dict_does_not_have_variant_when_variant_is_not_given():
    flag = FeatureFlag('xyz')

    assert flag.to_dict() == {'featureFlag': 'xyz'}


def test_feature_flag_dict_does_not_have_variant_when_variant_is_none():
    flag = FeatureFlag('abc', variant=None)

    assert flag.to_dict() == {'featureFlag': 'abc'}


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


def test_feature_flags_are_comparable():
    flag1 = FeatureFlag('a')
    flag2 = FeatureFlag('b', 'x')
    flag3 = FeatureFlag('c')

    assert flag1 == FeatureFlag('a')
    assert flag2 == FeatureFlag('b', 'x')
    assert flag3 == FeatureFlag('c')

    assert flag1 != FeatureFlag('a', '1')
    assert flag2 != FeatureFlag('b')

    assert flag1 != flag2
    assert flag1 != flag3
    assert flag2 != flag3

    assert flag1 != 'a'
    assert flag1 is not None


def test_delegate_contains_no_flags_by_default():
    delegate = FeatureFlagDelegate()

    assert delegate.to_list() == []
    assert delegate.to_json() == []


def test_delegate_does_not_get_mutated_after_being_copied():
    delegate1 = FeatureFlagDelegate()
    delegate1.add('abc', '123')

    delegate2 = delegate1.copy()
    delegate2.add('xyz', '456')

    delegate3 = delegate2.copy()
    delegate3.clear()

    assert delegate1.to_json() == [{'featureFlag': 'abc', 'variant': '123'}]
    assert delegate2.to_json() == [
        {'featureFlag': 'abc', 'variant': '123'},
        {'featureFlag': 'xyz', 'variant': '456'},
    ]
    assert delegate3.to_json() == []


def test_delegate_can_add_flags_individually():
    delegate = FeatureFlagDelegate()
    delegate.add('abc', 'xyz')
    delegate.add('another', None)
    delegate.add('again', 123)

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': 'xyz'},
        {'featureFlag': 'another'},
        {'featureFlag': 'again', 'variant': '123'}
    ]


def test_delegate_add_replaces_by_name_when_the_original_has_no_variant():
    delegate = FeatureFlagDelegate()
    delegate.add('abc', None)
    delegate.add('another', None)
    delegate.add('abc', 123)

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': '123'},
        {'featureFlag': 'another'}
    ]


def test_delegate_add_replaces_by_name_when_the_replacement_has_no_variant():
    delegate = FeatureFlagDelegate()
    delegate.add('abc', '123')
    delegate.add('another', None)
    delegate.add('abc', None)

    assert delegate.to_json() == [
        {'featureFlag': 'abc'},
        {'featureFlag': 'another'}
    ]


def test_delegate_add_replaces_by_name_when_both_have_variants():
    delegate = FeatureFlagDelegate()
    delegate.add('abc', '123')
    delegate.add('another', None)
    delegate.add('abc', '456')

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': '456'},
        {'featureFlag': 'another'}
    ]


@pytest.mark.parametrize('invalid_name', _invalid_names)
def test_delegate_add_add_drops_flag_when_name_is_invalid(invalid_name):
    delegate = FeatureFlagDelegate()
    delegate.add('abc', '123')
    delegate.add(invalid_name, None)

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': '123'}
    ]


def test_delegate_can_add_multiple_flags_at_once():
    delegate = FeatureFlagDelegate()
    delegate.merge([
        FeatureFlag('a', 'xyz'),
        FeatureFlag('b'),
        FeatureFlag('c', '111'),
        FeatureFlag('d'),
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'a', 'variant': 'xyz'},
        {'featureFlag': 'b'},
        {'featureFlag': 'c', 'variant': '111'},
        {'featureFlag': 'd'}
    ]


def test_delegate_can_merge_new_flags_with_existing_ones():
    delegate = FeatureFlagDelegate()
    delegate.merge([
        FeatureFlag('a', 'xyz'),
        FeatureFlag('b'),
        FeatureFlag('c', '111'),
        FeatureFlag('d'),
    ])

    delegate.merge([
        FeatureFlag('e'),
        FeatureFlag('a'),
        FeatureFlag('d', 'xyz'),
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'a'},
        {'featureFlag': 'b'},
        {'featureFlag': 'c', 'variant': '111'},
        {'featureFlag': 'd', 'variant': 'xyz'},
        {'featureFlag': 'e'}
    ]


def test_delegate_merge_replaces_by_name_when_the_original_has_no_variant():
    delegate = FeatureFlagDelegate()

    delegate.add('a', None)
    delegate.merge([
        FeatureFlag('a', 'xyz'),
        FeatureFlag('b'),
        FeatureFlag('c', '111'),
        FeatureFlag('d'),
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'a', 'variant': 'xyz'},
        {'featureFlag': 'b'},
        {'featureFlag': 'c', 'variant': '111'},
        {'featureFlag': 'd'}
    ]


def test_delegate_merge_replaces_by_name_when_the_replacement_has_no_variant():
    delegate = FeatureFlagDelegate()

    delegate.add('a', 'xyz')
    delegate.merge([
        FeatureFlag('a', None),
        FeatureFlag('b'),
        FeatureFlag('c', '111'),
        FeatureFlag('d'),
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'a'},
        {'featureFlag': 'b'},
        {'featureFlag': 'c', 'variant': '111'},
        {'featureFlag': 'd'}
    ]


def test_delegate_merge_replaces_by_name_when_both_have_variants():
    delegate = FeatureFlagDelegate()

    delegate.add('a', 'xyz')
    delegate.merge([
        FeatureFlag('a', 'abc'),
        FeatureFlag('b'),
        FeatureFlag('c', '111'),
        FeatureFlag('d'),
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'a', 'variant': 'abc'},
        {'featureFlag': 'b'},
        {'featureFlag': 'c', 'variant': '111'},
        {'featureFlag': 'd'}
    ]


def test_delegate_merge_ignores_anything_that_isnt_a_feature_flag_instance():
    delegate = FeatureFlagDelegate()

    delegate.merge([
        FeatureFlag('a', None),
        1234,
        FeatureFlag('b'),
        'hello',
        FeatureFlag('c', '111'),
        Exception(':)'),
        FeatureFlag('d'),
        None
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'a'},
        {'featureFlag': 'b'},
        {'featureFlag': 'c', 'variant': '111'},
        {'featureFlag': 'd'}
    ]


@pytest.mark.parametrize('invalid_name', _invalid_names)
def test_delegate_merge_drops_flag_when_name_is_invalid(invalid_name):
    delegate = FeatureFlagDelegate()
    delegate.merge([
        FeatureFlag('abc', '123'),
        FeatureFlag(invalid_name, '456'),
        FeatureFlag('xyz', '789')
    ])

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': '123'},
        {'featureFlag': 'xyz', 'variant': '789'}
    ]


def test_delegate_can_remove_flags_by_name():
    delegate = FeatureFlagDelegate()
    delegate.merge([
        FeatureFlag('abc', '123'),
        FeatureFlag('to be removed', '456'),
        FeatureFlag('xyz', '789')
    ])

    delegate.remove('to be removed')

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': '123'},
        {'featureFlag': 'xyz', 'variant': '789'}
    ]


def test_delegate_remove_does_nothing_when_no_flag_has_the_given_name():
    delegate = FeatureFlagDelegate()
    delegate.merge([
        FeatureFlag('abc', '123'),
        FeatureFlag('to be kept', '456'),
        FeatureFlag('xyz', '789')
    ])

    delegate.remove('to be removed')

    assert delegate.to_json() == [
        {'featureFlag': 'abc', 'variant': '123'},
        {'featureFlag': 'to be kept', 'variant': '456'},
        {'featureFlag': 'xyz', 'variant': '789'}
    ]


def test_delegate_can_remove_all_flags_at_once():
    delegate = FeatureFlagDelegate()
    delegate.merge([
        FeatureFlag('abc', '123'),
        FeatureFlag('to be kept', '456'),
        FeatureFlag('xyz', '789')
    ])

    delegate.clear()

    assert delegate.to_json() == []


def test_delegate_clear_does_nothing_when_there_are_no_flags():
    delegate = FeatureFlagDelegate()
    delegate.clear()

    assert delegate.to_json() == []


def test_delegate_to_list_returns_a_list_of_feature_flags():
    delegate = FeatureFlagDelegate()
    delegate.merge([FeatureFlag('a'), FeatureFlag('b'), FeatureFlag('c')])

    assert delegate.to_list() == [
        FeatureFlag('a'),
        FeatureFlag('b'),
        FeatureFlag('c')
    ]


def test_delegate_can_be_mutated_without_affecting_the_internal_storage():
    delegate = FeatureFlagDelegate()
    delegate.merge([FeatureFlag('a'), FeatureFlag('b')])

    flags = delegate.to_list()
    flags.pop()
    flags.append(1234)
    flags.append(5678)

    assert flags == [FeatureFlag('a'), 1234, 5678]
    assert delegate.to_list() == [FeatureFlag('a'), FeatureFlag('b')]
