import pytest

from bugsnag import RequestConfiguration


def test_request_config_meta_data_warns():
    config = RequestConfiguration.get_instance()

    with pytest.warns(DeprecationWarning) as records:
        config.meta_data['foo'] = 'bar'
        assert len(records) == 1
        assert str(records[0].message) == ('RequestConfiguration.meta_data ' +
                                           'has been renamed to "metadata"')
    assert config.metadata['foo'] == 'bar'
