import copy
import os
import shutil

from tests.api_tools import ApiClient
from tests.client_app_config import client_config


class EmployeeData(ApiClient):
    admin_user = copy.deepcopy(client_config.default_admin_user)
    employee1 = {
        'username': 'FF', 'firstname': 'Fred', 'lastname': 'Fisch', 'state': 'active', 'authentication_level': 0,
        'credential_hash': 'ff-pass'
    }
    employee2 = {
        'username': 'JT', 'firstname': 'John', 'lastname': 'Test', 'state': 'active', 'authentication_level': 1
    }
    employee2_inactive = {
        'state': 'inactive'
    }
    employee3 = {
        'username': 'AA', 'firstname': 'Anton', 'lastname': 'Admin', 'state': 'active', 'authentication_level': 2
    }
    employee4 = {
        'username': 'JD', 'firstname': 'Jeff', 'lastname': 'Deleteme', 'state': 'active', 'authentication_level': 99
    }
    employee5 = {
        'username': 'min', 'state': 'inactive', 'authentication_level': 3
    }

    fail_list = [
        {'username': 'FF', 'state': 'active', 'authentication_level': 0},  # should fail because of the same username
        {'firstname': 'Fred', 'lastname': 'Fisch', 'state': 'active', 'authentication_level': 0},
        {'username': 'FF1', 'state': 'active'},
        {'state': 'active', 'authentication_level': 0},
        {'username': 'FF2', 'firstname': 'Fred', 'lastname': 'Fisch', 'authentication_level': 0},
        {'username': 'FF3', 'firstname': 'Fred', 'lastname': 'Fisch', 'state': 'active'},
        {'username': 'FF4', 'firstname': 'Fred', 'lastname': 'Fisch', 'state': 'active', 'authentication_level': 0,
         'test_col': 'fail'}
    ]

    def __init__(self):
        ApiClient.__init__(self, 'users')
        self.db_spec = client_config.db_spec
        self.customview_spec = client_config.customview_spec
        self.id_admin_user = None
        self.id_employee1 = None
        self.id_employee2 = None
        self.id_employee3 = None
        self.id_employee4 = None
        self.id_employee5 = None

    def initial_data(self):
        # as default at least an admin user has been created -> use it
        self.query_size(1)
        self._check_write_blocked()
        self.query_size(1)  # still just the admin user should exist, nothing more

        self.login_admin()  # assertion if failed
        self._create_tests()
        self.query_size(6)

    def extended_tests(self):
        self._fail_tests()
        self._modify_tests()
        self._remove_tests()
        self._authentication_tests()

    def _check_write_blocked(self):
        # this write access should fail because there is no token yet
        self.api_create_entry(0, self.employee1, expected_result=401, do_token_auth=True)

        # this write access should fail because a token is needed for write access
        self.api_create_entry(0, self.employee1, expected_result=401, do_token_auth=False)

    def _create_tests(self):
        # this write access should fail because no token is sent even we're logged in
        self.api_create_entry(0, self.employee1, expected_result=401, do_token_auth=False)

        self.query_size(1)  # still just the admin user should exist, nothing more

        reply = self.api_create_entry(0, self.employee1)
        self.check_reply(reply, self.employee1, skip_fields=['credential_hash'])
        self.id_employee1 = self.get_primary_id(reply, self.db_spec)

        reply = self.api_create_entry(0, self.employee2)
        self.check_reply(reply, self.employee2)
        self.id_employee2 = self.get_primary_id(reply, self.db_spec)

        assert self.id_employee2 == (self.id_employee1 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_employee1, self.id_employee2)

        reply = self.api_create_entry(0, self.employee3)
        self.check_reply(reply, self.employee3)
        self.id_employee3 = self.get_primary_id(reply, self.db_spec)

        assert self.id_employee3 == (self.id_employee2 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_employee2, self.id_employee3)

        reply = self.api_create_entry(0, self.employee4)
        self.check_reply(reply, self.employee4)
        self.id_employee4 = self.get_primary_id(reply, self.db_spec)

        assert self.id_employee4 == (self.id_employee3 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_employee3, self.id_employee4)

        reply = self.api_create_entry(0, self.employee5)
        self.check_reply(reply, self.employee5)
        self.id_employee5 = self.get_primary_id(reply, self.db_spec)

        assert self.id_employee5 == (self.id_employee4 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_employee4, self.id_employee5)

        self._check_all_entries_after_creation()

    def _check_all_entries_after_creation(self):
        query_result = self.api_request_get(args=None)
        assert 'data' in query_result, 'No data field in query result: {0}'.format(query_result)
        assert len(query_result['data']) > 0, 'Users query result is empty'

        # first entry must be the default-created admin user -> get the id out of it
        self.id_admin_user = self.get_primary_id(query_result['data'][0], self.db_spec)
        del self.admin_user['password']

        expected_tables = {
            'users': [(self.id_admin_user, self.admin_user), (self.id_employee1, self.employee1),
                      (self.id_employee2, self.employee2), (self.id_employee3, self.employee3),
                      (self.id_employee4, self.employee4), (self.id_employee5, self.employee5)]
        }

        assert len(query_result['data']) == len(expected_tables['users']), 'Users query result has too few or too many rows'

        for entry in query_result['data']:
            for table_name in expected_tables:
                assert table_name in entry, 'Table \'{0}\' not in users query: {1}'.format(table_name, entry)
                self.extended_check_db_content(self.db_spec, self.customview_spec, table_name, entry[table_name],
                                               expected_tables[table_name])

    def _fail_tests(self):
        for row in self.fail_list:
            reply = self.api_create_entry(0, row, 400)

        self.query_size(6)

    def _modify_tests(self):
        updated_empl2 = self.employee2.copy()
        updated_empl2.update(self.employee2_inactive)
        reply = self.api_edit_entry(self.id_employee2, updated_empl2)

        self.check_reply(reply, updated_empl2)

        employee2_id_result = self.get_primary_id(reply, self.db_spec)
        assert employee2_id_result == self.id_employee2,\
            'primary key changed after SQL update! (table: {0} pre:{1} post:{2})'\
            .format(self.resource_name, self.id_employee2, employee2_id_result)

        # the dict of user2 has been changed; correct it because it will be checked in api_orderings
        self.employee2.update(self.employee2_inactive)

    def _remove_tests(self):
        # remove self.employee4

        reply = self.api_remove_entry(self.id_employee4, self.employee4)  # remove using the data field also
        # <---- TODO: what should be replied from a remove?
        # assert reply
        self.query_size(5)
        self.id_employee4 = None

        # insert 4 again to delete it an other way
        reply = self.api_create_entry(0, self.employee4)
        self.check_reply(reply, self.employee4)
        self.id_employee4 = self.get_primary_id(reply, self.db_spec)
        self.query_size(6)

        reply = self.api_remove_entry(self.id_employee4)  # remove just with the ID
        self.query_size(5)
        self.id_employee4 = None

    def _authentication_tests(self):
        self._logout()

        # not allowed to delete anything if not logged in (anymore)
        self.api_remove_entry(self.id_employee3, self.employee3, expected_result=401)
        self.query_size(5)

        # not allowed to create an employee if logged out
        self.api_create_entry(0, self.employee4, expected_result=401)

        user_pass = '{0}:{1}'.format(self.employee1['username'], 'ff-pass')
        self.login(user_pass=user_pass)  # assertion if failed

        # not allowed to create an employee as unauthorized user
        self.api_create_entry(0, self.employee4, expected_result=401)

        self._logout()

        # not allowed to create an employee as unauthorized user
        self.api_create_entry(0, self.employee4, expected_result=401)

        # now login as admin and check if a different logout also works
        self.login_admin()  # assertion if failed
        self._logout_any_api()  # logout on a different API call than the token auth

        # not allowed to create an employee as unauthorized user
        self.api_create_entry(0, self.employee4, expected_result=401)
        self.api_remove_entry(self.id_employee2, expected_result=401)

        # session remove test: remove the session storage folder and check if the session gets invalid
        self.login_admin()
        shutil.rmtree(client_config.session_dir)
        os.makedirs(client_config.session_dir)
        # session key is lost; do not allow to use the admin session again
        self.api_remove_entry(self.id_employee2, expected_result=401)
        self.api_create_entry(0, self.employee4, expected_result=401)
        self._logout()

        self.api_remove_entry(self.id_employee2, expected_result=401)

        # TODO: do more authentication checks to cover all cases! flask_squirrel/util/own_auth.py 73%
        # 167, 195, 199,
        # 201, 205-207, 224, 232, 240, 247, 254-257, 261, 269, 275-278, 283-287, 301-304, 316, 318, 320, 326, 329,
        # 337-338, 346-347, 361-362, 368-369, 385-386, 398-399, 445, 447, 449, 452-454, 458, 463-466, 470, 474-476,
        # 482, 494, 505, 151->153, 165->167, 198->199, 200->201, 223->224, 231->232, 239->240, 245->247, 260->261,
        # 267->269, 282->283, 289->306, 315->316, 317->318, 319->320, 325->326, 328->329, 345->346, 367->368,
        # 397->398, 408->420, 417->420, 444->445, 446->447, 448->449, 451->452, 457->458, 462->463, 469->470,
        # 473->474, 480->482, 493->494, 498->505, 500->505
        # TODO: configure token timeout


empl_api = EmployeeData()
