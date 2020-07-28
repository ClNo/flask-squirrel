import base64
import datetime
import json

from werkzeug import test
from typing import Dict, Union, Optional

from flask_squirrel.table.dbutil import get_primarykey_colname
from tests.client_app_config import client_config

test_client: Optional[test.Client] = None
DEFAULT_ARGS: Dict[str, Union[int, str]] = {'version': 1, 'language': 'en'}
LOGIN_ROUTE: str = 'login-token'


def to_date(iso: str):
    return datetime.datetime.strptime(iso, '%Y-%m-%d').date()


class ApiClient:

    def __init__(self, resource_name: str, default_args: Optional[Dict[str, Union[int, str]]] = None):
        self.client: test.Client = test_client
        self.resource_name: str = resource_name
        if default_args:
            self.default_args: Dict[str, Union[int, str]] = default_args
        else:
            self.default_args: Dict[str, Union[int, str]] = DEFAULT_ARGS
        self.res_path: str = '/{0}/{1}'.format(client_config.api_path, self.resource_name)
        self.token: Optional[str] = None

        self.default_args['get'] = 'data_spec'  # always query data and the spec at the same time for now
        # todo: do tests with data and spec separated also

    def set_api_path(self, resource_name: str):
        self.resource_name = resource_name
        self.res_path: str = '/{0}/{1}'.format(client_config.api_path, self.resource_name)

    def api_request_get(self, expected_result=200, args=None):
        query_dict = self.default_args.copy()
        if args:
            query_dict.update(args)
        rv = self.client.get(self.res_path, query_string=query_dict)
        assert rv.status_code == expected_result, '{0} not found: {1}'.format(self.resource_name, rv.status)

        try:
            json_data = rv.json
        except Exception as e:
            assert False, 'error parsing JSON data in {0}: {1}'.format(self.resource_name, e)

        return json_data

    def api_create_entry(self, entry_id: int, fields, expected_result=200, do_token_auth=True, fail_text=None):
        req_data = self.generate_request_data('create', entry_id, self.resource_name, fields)  # resource_name is also the table_name (!?)
        headers = None
        if do_token_auth and self.token:
            headers = {'Authorization': 'Bearer ' + self.token}

        # print('req_data', req_data)
        rv = self.client.post(self.res_path, data=req_data, headers=headers)

        err_msg = ''
        try:
            err_msg = rv.json['error']
        except:
            pass

        assert rv.status_code == expected_result, 'POST/create to {0} not succeed, http response: {1}\ncommand: {2}\n{3}\n{4}'\
            .format(self.resource_name, rv.status, req_data, fail_text, err_msg)

        if expected_result != 200:
            return rv.json

        assert rv.data, 'POST to {0} return empty data: {1}\ncommand: {2}\n{3}'\
            .format(self.resource_name, req_data, err_msg)

        return rv.json['data']

    def api_edit_entry(self, entry_id: int, fields, expected_result=200, do_token_auth=True):
        req_data = self.generate_request_data('edit', entry_id, self.resource_name,
                                              fields)  # resource_name is also the table_name (!?)
        headers = None
        if do_token_auth and self.token:
            headers = {'Authorization': 'Bearer ' + self.token}

        # print('req_data', req_data)
        rv = self.client.post(self.res_path, data=req_data, headers=headers)
        if rv.status_code != expected_result:
            msg = 'POST/edit to {0} not succeed, http response: {1}\ncommand: {2}' \
                  .format(self.resource_name, rv.status, req_data)
            if rv.json and 'error' in rv.json:
                msg += '\nERROR: {0}'.format(rv.json['error'])
        assert rv.status_code == expected_result, msg

        if expected_result != 200:
            return rv.json

        assert rv.data, 'POST to {0} return empty data: {1}\ncommand: {2}' \
            .format(self.resource_name, req_data)

        return rv.json['data']

    def api_remove_entry(self, entry_id: int, fields=None, expected_result=200, do_token_auth=True):
        req_data = self.generate_request_data('remove', entry_id, self.resource_name, fields)
        headers = None
        if do_token_auth and self.token:
            headers = {'Authorization': 'Bearer ' + self.token}

        rv = self.client.post(self.res_path, data=req_data, headers=headers)
        assert rv.status_code == expected_result, 'POST/delete to {0} not succeed, http response: {1}\ncommand: {2}' \
            .format(self.resource_name, rv.status, req_data)

        if expected_result != 200:
            return rv.json

        assert rv.data, 'POST to {0} return empty data: {1}\ncommand: {2}' \
            .format(self.resource_name, req_data)

        return rv.json['data']

    def query_size(self, expected_size, args=None):
        query_result = self.api_request_get(args=args)
        assert 'data' in query_result, 'resource {0} should contain a \'data\' field'.format(self.resource_name)
        table_entries = query_result['data']
        assert len(table_entries) == expected_size, 'resource {0} should contain {1} entries, returned size: {2}, data: {3}' \
            .format(self.resource_name, expected_size, len(table_entries), table_entries)

    def query_elements(self, args):
        query_result = self.api_request_get(args=args)
        assert 'data' in query_result, 'resource {0} should contain a \'data\' field'.format(self.resource_name)
        table_entries = query_result['data']
        return table_entries

    def login_admin(self, should_succeed=True):
        valid_credentials = base64.b64encode(b'admin:adm123').decode('utf-8')
        self._internal_login(valid_credentials, should_succeed)

    def login(self, user_pass, should_succeed=True):
        valid_credentials = base64.b64encode(user_pass.encode()).decode('utf-8')
        self._internal_login(valid_credentials, should_succeed)

    def _internal_login(self, valid_credentials, should_succeed):

        login_route: str = '/{0}/{1}'.format(client_config.api_path, LOGIN_ROUTE)
        rv = self.client.get(login_route, headers={'Authorization': 'Basic ' + valid_credentials})
        if should_succeed:
            assert rv.status_code == 200, 'Authentication error: login as admin failed! {0}'.format(rv)

        if rv.status_code == 200:
            assert rv.data, 'Authentication error: login succeed, but no return data'
            data_dict = rv.json
            assert 'token' in data_dict, 'Authentication error: login succeed, but no token passed'
            assert len(data_dict['token']) >= 10, 'Authentication error: login succeed, but token is too short!'
            self.token = data_dict['token']
        else:
            self.token = None
        return self.token

    def _logout(self, should_succeed=True):
        login_route: str = '/{0}/{1}'.format(client_config.api_path, LOGIN_ROUTE)
        rv = self.client.get(login_route, query_string={'logout': True}, mimetype='application/json')  # , content_type='application/json')
        if should_succeed:
            assert rv.status_code == 200, 'Authentication error: logout failed! {0}'.format(rv)

        if rv.status_code == 200:
            assert rv.data, 'Authentication error: logout succeed, but no return data'
            self.token = None

    def _logout_any_api(self):
        # a 'logout' parameter should work everywhere
        login_route: str = '/{0}/{1}'.format(client_config.api_path, self.resource_name)
        rv = self.client.get(login_route, query_string={'logout': True}, mimetype='application/json')  # , content_type='application/json')
        assert rv.status_code == 200, 'Authentication error: logout failed! {0}'.format(rv)

        # the answer should be empty and not contain any data!
        try:
            assert rv.data, 'Authentication error: logout succeed, but no return data'
            data_dict = rv.json
            assert len(data_dict) > 0, 'Authentication error: logout succeed, but no return data'
        except:
            pass

    @staticmethod
    def generate_request_data(action: str, entry_id: int, table_name: str, fields=None):
        req = {'action': action}
        if fields:
            for key in fields:
                # the key format is quite a little bit unexpected
                key_name = 'data[{0}][{1}][{2}]'.format(entry_id, table_name, key)
                req[key_name] = fields[key]
        else:
            # field could be null for delete/remove commands
            key_name = 'data[{0}][{1}]'.format(entry_id, table_name)
            req[key_name] = ''
        return json.dumps(req)

    def check_reply(self, reply, request_data, skip_fields=None):
        if type(reply) == list:
            reply_data = reply[0]
        elif type(reply) == dict:
            reply_data = reply
        else:
            assert False, 'Unsupported reply type {0} of reply: {1}'.format(type(reply), reply)

        assert self.resource_name in reply_data, 'Table {0} not in reply {1}'.format(self.resource_name, reply_data)
        for field in request_data:
            if (not skip_fields) or (field not in skip_fields):
                assert field in reply_data[self.resource_name], 'Field \'{0}\' not in reply {1}'.format(field, reply_data)
                assert str(reply_data[self.resource_name][field]) == str(request_data[field]),\
                    'Field {0} not equal - original: {1} - db reply: {2}'.format(field, request_data[field],
                                                                                 reply_data[self.resource_name][field])

    def get_primary_id(self, reply, db_spec):
        if type(reply) == list:
            reply_data = reply[0]
        elif type(reply) == dict:
            reply_data = reply

        primary_colname = get_primarykey_colname(self.resource_name, db_spec)
        assert primary_colname in reply_data[self.resource_name], 'Primary key {0} not found in reply {1}'.format(primary_colname, reply_data)
        primary_id = reply_data[self.resource_name][primary_colname]
        assert type(primary_id) == int, 'Primary key {0} is not of type int! (type: {1})'.format(primary_colname, type(primary_id))
        return primary_id

    @staticmethod
    def extended_check_db_content(db_spec, customview_spec, table_name, db_entry, source_list):
        from flask_squirrel.table import dbutil
        primary_key = dbutil.get_primarykey_colname(table_name, db_spec)
        assert primary_key in db_entry, 'Query response does not contain the primary key \'{0}\': {1}'.format(primary_key, db_entry)
        primary_id = db_entry[primary_key]
        assert primary_key is not None, 'Query response contains an empty primary key \'{0}\': {1}'.format(primary_key, db_entry)
        source_entry = [entry for prim_id, entry in source_list if prim_id == primary_id]
        assert len(source_entry) == 1, 'There is an entry in the query result which is not expected! Is the source dict complete? Unexpected DB entry: {0}'.format(db_entry)

        # now compare all source dict columns/field source_entry against db_entry!
        source_dict = source_entry[0]
        for field in source_dict:
            assert field in db_entry, 'Query response does not contain the column \'{0}\': {1}'.format(field, db_entry)
            is_password = False
            if field in customview_spec[table_name]:
                if '_attributes' in customview_spec[table_name][field]:
                    if 'password' in customview_spec[table_name][field]['_attributes']:
                        is_password = True
            if not is_password:
                assert db_entry[field] == source_dict[field], 'Query response column \'{0}\' is not equal to \'{1}\': {2}'.format(field, source_dict[field], db_entry)
            else:
                # check if password is empty!
                str_len = len(db_entry[field])
                assert (str_len == 0) or (db_entry[field].count('*') == str_len) or (db_entry[field].count('-') == str_len), 'Password field is not empty!'
