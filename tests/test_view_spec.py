import json
from tests.client_app_config import client_config


def test_resource_view_spec(client):
    """Test resource spec."""

    # for client API see: https://werkzeug.palletsprojects.com/en/0.15.x/test/#werkzeug.test.Client
    rv = client.get('/{0}/resource-view-spec'.format(client_config.api_path))
    # rv = client.get('/squirrel/resource-view-spec')

    assert rv.status_code == 200, 'resource-view-spec not found: {0}'.format(rv.status)

    try:
        resource_view_spec = json.loads(rv.data)['data']  # unclear why there is this data field
    except Exception as e:
        assert False, 'error parsing JSON data in resource-view-spec: {0}'.format(e)

    assert resource_view_spec, 'resource-view-spec passes empty result'
    assert len(resource_view_spec.keys()) >= 3, 'resource-view-spec contains less than 3 tables'

    # now check every table!
    for table_name in resource_view_spec:
        check_table_view_spec(table_name, resource_view_spec[table_name])

    # allowed_version_chars = '0123456789.'
    # if not all((c in allowed_version_chars) for c in status['version']):
    #     assert 'Chars in version which are not allowed! Allowed chars: {0}'.format(allowed_version_chars)


def check_table_view_spec(table_name, table_spec):
    assert table_name, 'table name not set'
    assert table_spec, 'table {0} has no entries'.format(table_name)
    assert table_spec['label'], 'no label in table {0}'.format(table_name)
    # not required any more: assert 'table-fields' in table_spec
    # not required any more: assert 'editor-fields' in table_spec
