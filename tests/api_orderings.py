from datetime import timedelta, date
from flask_squirrel.table.dbutil import get_label_for_lang
from tests.api_tools import ApiClient
from tests.client_app_config import client_config
from tests.api_employees import empl_api
from tests.api_projects import proj_api
from tests.api_suppliers import suppl_api


class OrderingsData(ApiClient):
    TODAY_ISO = (date.today() - timedelta(days=1)).isoformat()
    YEARS_BEFORE_ISO = (date.today() - timedelta(days=(4*365))).isoformat()

    order1 = {
        'order_nameid': 'Order ABC 2019-10 A', 'idsupplier': suppl_api.id_supplier1, 'material': 'Mat String 123',
        'idproject': proj_api.id_project1, 'idemployee_ordered': empl_api.id_employee1,
        'order_state': 'ordered',
        'date_ordered': TODAY_ISO, 'date_invoice_planned': '2019-11-05', 'invoice': '556677.55'
    }
    order2 = {
        'order_nameid': 'Order DEF 2019-03 B', 'idsupplier': suppl_api.id_supplier1, 'material': 'Mat String 456',
        'idproject': proj_api.id_project2, 'idemployee_ordered': empl_api.id_employee2,
        'order_state': 'ordered',
        'date_ordered': TODAY_ISO, 'date_invoice_planned': '2019-11-05', 'invoice': '3344.75'  # <------ .70 fails!
    }
    order3 = {
        'order_nameid': 'Order GHI 2018-01 A', 'idsupplier': suppl_api.id_supplier2, 'material': 'Mat String 789',
        'idproject': proj_api.id_project3, 'idemployee_ordered': empl_api.id_employee3,
        'order_state': 'ordered',
        'date_ordered': YEARS_BEFORE_ISO, 'date_invoice_planned': '2019-11-05', 'invoice': '55'  # <------ .00 fails!
    }
    order4 = {
        'order_nameid': 'Order JKL 2020-01 A', 'idsupplier': suppl_api.id_supplier2, 'material': 'Mat String 1122',
        'idproject': proj_api.id_project3, 'idemployee_ordered': empl_api.id_employee3,
        'order_state': 'ordered',
        'date_ordered': YEARS_BEFORE_ISO, 'date_invoice_planned': '20209-11-05', 'invoice': '55'  # <------ .00 fails!
    }

    def __init__(self):
        ApiClient.__init__(self, 'orderings')
        self.db_spec = client_config.db_spec
        self.customview_spec = client_config.customview_spec
        self.translation_spec = client_config.translation_spec
        self.id_order1 = None
        self.id_order2 = None
        self.id_order3 = None
        self.id_order4 = None

    def initial_data(self):
        self.query_size(expected_size=0, args={'predef_filter': 'projects-all'})  # TODO: query makes no sense here!
        self._create_tests()
        self.query_size(expected_size=2, args={'predef_filter': 'projects-running'})
        self.query_size(expected_size=1, args={'predef_filter': 'projects-finished'})

    def _create_tests(self):
        reply = self.api_create_entry(0, self.order1)
        self.check_reply(reply, self.order1)
        self.id_order1 = self.get_primary_id(reply, self.db_spec)

        reply = self.api_create_entry(0, self.order2)
        self.check_reply(reply, self.order2)
        self.id_order2 = self.get_primary_id(reply, self.db_spec)

        assert self.id_order2 == (self.id_order1 + 1),\
            'primary key of {0} not auto incrementing (id1:{1} id2:{2})'.format(self.resource_name, self.id_order1, self.id_order2)

        reply = self.api_create_entry(0, self.order3)
        self.check_reply(reply, self.order3)
        self.id_order3 = self.get_primary_id(reply, self.db_spec)

        assert self.id_order3 == (self.id_order2 + 1),\
            'primary key of {0} not auto incrementing (id2:{1} id3:{2})'.format(self.resource_name, self.id_order2, self.id_order3)

    def verbose_content_check(self):
        query_result = self.api_request_get(args=None)  # get all orderings which is the most complex table
        assert len(query_result) > 0, 'Orderings query result is empty'

        # {'data': [{'orderings': {'idordering': 1, 'order_nameid': 'Order ABC 2019-10 A', 'idsupplier': 1,
        # 'material': 'Mat String 123', 'idproject': 1, 'idemployee_ordered': 2, 'order_state': 'ordered',
        # 'date_ordered': '2019-09-04', 'date_invoice_planned': '2019-11-05', 'date_planned': None, 'date_delivered':
        # None, 'date_invoiced_done': None, 'invoice': '556677.55', 'comment': None}, 'DT_RowId': 1, 'suppliers': {
        # 'idsupplier': 1, 'name': 'Max Supplier'}, 'projects': {'idproject': 1, 'name': 'Proj ABC 2019-10 A',
        # 'comment': 'Comment 2019', 'project_state': 'running', 'date_started': '2019-09-04', 'date_finished':
        # None}, 'users': {'iduser': 2, 'username': 'FF', 'firstname': 'Fred', 'lastname': 'Fisch',
        # 'credential_hash': '$6$rounds=656000$ZNHtqp027G7Z7FUd$kD6CP5.Y61AeauCpfHc56z8FgdVyHV4oPm6iAH7F46
        # /vPdzcohKX5iXYljTlsmKKgHoNMWvNWRlMjGw5lREGH0', 'authentication_level': 0, 'state': 'active'},
        # 'orderings_order_state': {'name': 'ordered'}}, {'orderings': {'idordering': 2, 'order_nameid': 'Order DEF
        # 2019-03 B', 'idsupplier': 1, 'material': 'Mat String 456', 'idproject': 2, 'idemployee_ordered': 3,
        # 'order_state': 'ordered', 'date_ordered': '2019-09-04', 'date_invoice_planned': '2019-11-05',
        # 'date_planned': None, 'date_delivered': None, 'date_invoiced_done': None, 'invoice': '3344.75', 'comment':
        # None}, 'DT_RowId': 2, 'suppliers': {'idsupplier': 1, 'name': 'Max Supplier'}, 'projects': {'idproject': 2,
        # 'name': 'Proj DEF 2020-11 B', 'comment': None, 'project_state': 'running', 'date_started': None,
        # 'date_finished': None}, 'users': {'iduser': 3, 'username': 'JT', 'firstname': 'John', 'lastname': 'Test',
        # 'credential_hash': None, 'authentication_level': 1, 'state': 'inactive'}, 'orderings_order_state': {'name':
        # 'ordered'}}, {'orderings': {'idordering': 3, 'order_nameid': 'Order GHI 2018-01 A', 'idsupplier': 2,
        # 'material': 'Mat String 789', 'idproject': 3, 'idemployee_ordered': 4, 'order_state': 'ordered',
        # 'date_ordered': '2019-09-04', 'date_invoice_planned': '2019-11-05', 'date_planned': None, 'date_delivered':
        # None, 'date_invoiced_done': None, 'invoice': '55', 'comment': None}, 'DT_RowId': 3, 'suppliers': {
        # 'idsupplier': 2, 'name': 'Supplier 123 456'}, 'projects': {'idproject': 3, 'name': 'Proj XYZ 2015-01 X',
        # 'comment': None, 'project_state': 'finished', 'date_started': '2015-01-04', 'date_finished': '2018-03-05'},
        # 'users': {'iduser': 4, 'username': 'AA', 'firstname': 'Anton', 'lastname': 'Admin', 'credential_hash':
        # None, 'authentication_level': 2, 'state': 'active'}, 'orderings_order_state': {'name': 'ordered'}}],

        # 'options': ...
        # 'filters': ...
        # 'translation': ...

        # 'label': 'Orderings',
        # query language is English by default
        assert 'label' in query_result, '\'label\' not found in query reply'.format(query_result)
        assert query_result['label'] == 'Orderings', 'Label in query reply is not \'Orderings\''

        # --- 1. check the data field ---
        expected_tables = {
            'orderings': [(self.id_order1, self.order1), (self.id_order2, self.order2), (self.id_order3, self.order3)],
            'suppliers': [(suppl_api.id_supplier1, suppl_api.supplier1), (suppl_api.id_supplier2, suppl_api.supplier2)],
            'projects': [(proj_api.id_project1, proj_api.project1), (proj_api.id_project2, proj_api.project2),
                         (proj_api.id_project3, proj_api.project3)],
            'users': [(empl_api.id_employee1, empl_api.employee1), (empl_api.id_employee2, empl_api.employee2),
                      (empl_api.id_employee3, empl_api.employee3)]
        }
        for entry in query_result['data']:
            for table_name in expected_tables:
                assert table_name in entry, 'Table \'{0}\' not in orderings query: {1}'.format(table_name, entry)
                if table_name == self.resource_name:
                    # the row of the main table is just a dict
                    self.extended_check_db_content(self.db_spec, self.customview_spec, table_name, entry[table_name],
                                                   expected_tables[table_name])

                else:
                    # entry[table_name] is a list of multiple ref_table entries of the same type
                    for joined_entry in entry[table_name]:
                        self.extended_check_db_content(self.db_spec, self.customview_spec, table_name, joined_entry,
                                                       expected_tables[table_name])

        # --- 2. check the options field (used for editing) ---
        assert 'options' in query_result, 'The orderings GET query did not contain a \'options\' entry'
        self._options_check(query_result['options'])

        # --- 3. check the translations field ---
        assert 'translation' in query_result, 'The orderings GET query did not contain a \'translation\' entry'
        self._translation_check(query_result['translation'])

        # --- 4. filter check ---
        assert 'filters' in query_result, 'The orderings GET query did not contain a \'filters\' entry'
        self._filter_check(query_result['filters'])

        # --- 5. check the editor fields ---
        assert 'editor-fields' in query_result, 'The orderings GET query did not contain a \'editor-fields\' entry'
        self._editor_fields_check(query_result['editor-fields'])

        # --- 6. check table fields (column specification)
        assert 'table-fields' in query_result, 'The orderings GET query did not contain a \'table-fields\' entry'
        self._table_fields_check(query_result['table-fields'], 'en')

        # --- 7. does the table specification match to the sent data?
        self._compare_data_to_table_fields(query_result['data'], query_result['table-fields'])

        # --- 8. different language -> check table fields (column specification)
        query_result = self.api_request_get(args={'lang': 'de'})  # get all orderings which is the most complex table
        assert len(query_result) > 0, 'Orderings query result is empty'
        self._table_fields_check(query_result['table-fields'], 'de')

        self._authentication_tests()

    def _filter_check(self, filters):
        # Note: this check depends on the date!

        # 'filters': [{'type': 'predefined', 'name': 'projects-running', 'default': True, 'translated_name': 'running
        # projects'}, {'type': 'predefined', 'name': 'projects-finished', 'default': False, 'translated_name':
        # 'finished projects only'}, {'type': 'predefined', 'name': 'projects-all', 'default': False,
        # 'translated_name': 'all projects'}, {'type': 'predefined', 'name': 'orderings-last-3-years', 'default':
        # False, 'translated_name': 'last 3 years'}],

        expected_filters = [('projects-running', 2), ('projects-finished', 1),
                            ('projects-all', 3), ('orderings-last-3-years', 2)]
        default_found = False
        for filter_name, count in expected_filters:
            filter_list = [f for f in filters if filter_name == f['name']]
            assert len(filter_list) == 1, 'Filter named \'{0}\' not found in query result: {1}'.format(filter_name, filters)
            filter_spec = filter_list[0]
            assert 'type' in filter_spec, 'Filter attribute \'type\' not in filter: {0}'.format(filter_spec)
            assert 'name' in filter_spec, 'Filter attribute \'name\' not in filter: {0}'.format(filter_spec)
            assert 'default' in filter_spec, 'Filter attribute \'default\' not in filter: {0}'.format(filter_spec)
            assert 'translated_name' in filter_spec, 'Filter attribute \'translated_name\' not in filter: {0}'.format(filter_spec)

            if filter_spec['default']:
                assert not default_found, 'Default filter found 2 times but should appear only once'
            default_found = default_found or filter_spec['default']

        assert default_found, 'No default filter found: {0}'.format(filters)

        for filter_name, count in expected_filters:
            query_result = self.api_request_get(args={'predef_filter': filter_name})
            assert len(query_result['data']) == count, 'Orderings query filter \'{0}\' should return {1} entries but gave {2}: {3}'.format(filter_name, count, len(query_result['data']), query_result['data'])

    def _options_check(self, options):
        # 'options': {'orderings.idsupplier': [{'label': '<undefiniert>', 'value': None}, {'label': 'Max Supplier',
        # 'value': 1}, {'label': 'Supplier 123 456', 'value': 2}], 'orderings.idproject': [{'label': '<undefiniert>',
        # 'value': None}, {'label': 'Proj ABC 2019-10 A', 'value': 1}, {'label': 'Proj DEF 2020-11 B', 'value': 2},
        # {'label': 'Proj XYZ 2015-01 X', 'value': 3}], 'orderings.idemployee_ordered': [{'label': '<undefiniert>',
        # 'value': None}, {'label': 'admin', 'value': 1}, {'label': 'FF', 'value': 2}, {'label': 'JT', 'value': 3},
        # {'label': 'AA', 'value': 4}, {'label': 'min', 'value': 6}], 'orderings.order_state': [{'label': 'ordered',
        # 'value': 'ordered'}, {'label': 'confirmed', 'value': 'confirmed'}, {'label': 'delivered',
        # 'value': 'delivered'}, {'label': 'invoiced', 'value': 'invoiced'}]},

        # check all the references of the table 'orderings' here
        ref_list = {
            'orderings.idsupplier': [None, suppl_api.id_supplier1, suppl_api.id_supplier2],
            'orderings.idproject': [None, proj_api.id_project1, proj_api.id_project2, proj_api.id_project3],
            'orderings.idemployee_ordered': [None, empl_api.id_admin_user, empl_api.id_employee1, empl_api.id_employee2,
                                             empl_api.id_employee3, empl_api.id_employee5],
            'orderings.order_state': None
        }
        for foreign_key in options:
            assert foreign_key in ref_list, 'Foreign key \'{0}\' not found in test list: {1}'.format(foreign_key, ref_list)
            entry_list = ref_list[foreign_key]  # could be 'None' for enums

            option_list = options[foreign_key]
            assert len(option_list) > 0, 'Option for {0} is empty'.format(foreign_key)

            for option in option_list:
                assert 'label' in option, 'Label not found in options list: {0}'.format(option)
                assert option['label'], 'Label is empty in options list: {0}'.format(option)
                assert len(option['label']), 'Label is emtpy: {0}'.format(option)
                assert 'value' in option, 'Value not found in options list: {0}'.format(option)

                # now check if the value exists in the ref_list
                if entry_list is not None:
                    found_entries = [e for e in entry_list if e == option['value']]
                    assert len(found_entries) == 1, 'Option value \'{0}\' not found in the list: {1}'.format(option['value'], entry_list)
                # else: this is an enum, check what?

    def _translation_check(self, translation):
        # 'translation': {'table_multi': 'Orderings', 'table_single': 'ordering', 'article': 'a'},

        expected_keys = ['table_multi', 'table_single', 'article']
        for key in expected_keys:
            assert key in translation, 'Key \'{0}\' not found in translation: {1}'.format(key, translation)

    def _editor_fields_check(self, editor_fields):
        # 'editor-fields': [{'name': 'orderings.order_nameid', 'label': 'Order number',
        # 'not-null': True}, {'name': 'orderings.idsupplier', 'label': 'Supplier', 'not-null': True,
        # 'type': 'select'}, {'name': 'orderings.material', 'label': 'Material'}, {'name': 'orderings.idproject',
        # 'label': 'Project', 'not-null': True, 'type': 'select'}, {'name': 'orderings.idemployee_ordered',
        # 'label': 'Who ordered', 'not-null': True, 'type': 'select'}, {'name': 'orderings.order_state',
        # 'label': 'Order state', 'not-null': True, 'type': 'select'}, {'name': 'orderings.date_ordered',
        # 'label': 'Date ordered', 'type': 'datetime'}, {'name': 'orderings.date_invoice_planned', 'label': 'Date
        # invoice planned', 'not-null': True, 'type': 'datetime'}, {'name': 'orderings.date_planned', 'label': 'Date
        # planned', 'type': 'datetime'}, {'name': 'orderings.date_delivered', 'label': 'Date delivered',
        # 'type': 'datetime'}, {'name': 'orderings.date_invoiced_done', 'label': 'Date invoiced',
        # 'type': 'datetime'}, {'name': 'orderings.invoice', 'label': 'Invoice amount', 'not-null': True},
        # {'name': 'orderings.comment', 'label': 'Comment'}],

        for field in editor_fields:
            assert 'name' in field, 'Key \'name\' not found in editor field: {0}'.format(field)
            assert 'label' in field, 'Key \'label\' not found in editor field: {0}'.format(field)
            # is optional: assert 'not-null' in field, 'Key \'not-null\' not found in editor field: {0}'.format(field)

        # check if every column has been sent with the request
        for column in self.db_spec[self.resource_name]['columns']:
            if column['func'] == 'primarykey':
                continue
            expected_name = '{0}.{1}'.format(self.resource_name, column['name'])
            found_fields = [f for f in editor_fields if f['name'] == expected_name]
            assert len(found_fields) == 1, 'Field \'{0}\' not found in editor fields: {1}'.format(expected_name, editor_fields)
            field = found_fields[0]
            assert 'label' in field, 'Attribute \'label\' not found in editor field: {0}'.format(field)
            assert len(field['label']) > 0, 'Attribute \'label\' is empty: {0}'.format(field)
            if 'not-null' in column:
                if column['not-null']:
                    assert 'not-null' in field, 'Field \'not-null\' should be set in: {0}'.format(field)
                    assert field['not-null'], 'Field \'not-null\' should be set: {0}'.format(field)
            if 'reference' in column:
                assert 'type' in field, 'Field \'type\' should be set in: {0}'.format(field)
                assert field['type'] == 'select', 'Field \'type\' should be a \'select\': {0}'.format(field)
            if column['type'] == 'date':
                assert 'type' in field, 'Field \'type\' should be set in: {0}'.format(field)
                assert field['type'] == 'datetime', 'Field \'type\' should be a \'datetime\': {0}'.format(field)

    def _table_fields_check(self, table_fields, current_lang):
        # 'table-fields': [{'data': 'orderings.order_nameid', 'title': 'Order number'}, {'data': 'suppliers.0.name',
        # 'title': 'Supplier'}, {'data': 'orderings.material', 'title': 'Material'}, {'data': 'projects.0.name',
        # 'title': 'Project'}, {'data': 'users.0.username', 'title': 'Who ordered'}, {'data':
        # 'orderings_order_state.name', 'title': 'Order state'}, {'data': 'orderings.date_ordered', 'title': 'Date
        # ordered', 'type': 'date'}, {'data': 'orderings.date_invoice_planned', 'title': 'Date invoice planned',
        # 'type': 'date'}, {'data': 'orderings.date_planned', 'title': 'Date planned', 'type': 'date'},
        # {'data': 'orderings.date_delivered', 'title': 'Date delivered', 'type': 'date'},
        # {'data': 'orderings.date_invoiced_done', 'title': 'Date invoiced', 'type': 'date'},
        # {'data': 'orderings.invoice', 'title': 'Invoice amount', 'type': 'num-fmt'}, {'data': 'orderings.comment',
        # 'title': 'Comment'}]

        for field in table_fields:
            assert 'data' in field, 'Key \'data\' not found in editor field: {0}'.format(field)
            assert 'title' in field, 'Key \'title\' not found in editor field: {0}'.format(field)

        ref_table_count = {}

        for column in self.db_spec[self.resource_name]['columns']:
            if column['func'] == 'primarykey':
                continue
            elif column['func'] == 'foreignkey':
                # this is a reference to an other table

                ref_table_name, ref_col_name = self.customview_spec[self.resource_name][column['name']]['ref_text'][0].split('.')

                if ref_table_name not in ref_table_count:
                    ref_table_count[ref_table_name] = 0
                expected_name = '{0}.{1}.{2}'.format(ref_table_name, ref_table_count[ref_table_name], ref_col_name)

            elif column['type'] == 'enum':
                expected_name = '{0}_{1}.name'.format(self.resource_name, column['name'])
                # Note: the underscore naming is a bit strange but it makes sense as it is some kind of a reference
                # not to an other table but to a list of possible selection items. Therefore a specific naming has
                # been introduced in dbtable.py.
            else:
                expected_name = '{0}.{1}'.format(self.resource_name, column['name'])
            found_fields = [f for f in table_fields if f['data'] == expected_name]
            assert len(found_fields) == 1, 'Field \'{0}\' not found in table fields: {1}'.format(expected_name, table_fields)

            # now check if the translation matches
            title = get_label_for_lang(current_lang, self.translation_spec[self.resource_name][column['name']])
            assert len(title) > 0, 'Translation for table {0} field {1} not done'.format(self.resource_name, found_fields[0])
            assert found_fields[0]['title'] == title, 'Title in table-fields is not \'{0}\': {1}'.format(title, found_fields[0])

    def _compare_data_to_table_fields(self, data, table_fields):
        # now we check if every table column/field appears in the data field
        for field in table_fields:
            field_parts = field['data'].split('.')
            table_name_parsed = field['data'].split('.')[0]

            if len(field_parts) == 2:
                ref_count_parsed = -1
                field_name_parsed = field_parts[1]
            else:
                ref_count_parsed = int(field_parts[1])
                field_name_parsed = field_parts[2]

            for entry in data:
                assert table_name_parsed in entry, 'Table name \'{0}\' should occur in the data field: {1}'.format(table_name_parsed, entry)

                if ref_count_parsed < 0:
                    found_fields = [f for f in entry[table_name_parsed] if f == field_name_parsed]
                    assert len(found_fields) == 1, 'Column \'{0}\' not found in data: {1}'.format(field_name_parsed, table_name_parsed)

                else:
                    found_fields = [f for f in entry[table_name_parsed][ref_count_parsed] if f == field_name_parsed]
                    assert len(found_fields) == 1, 'Column \'{0}\' not found in data: {1}'.format(field_name_parsed, table_name_parsed)

        # note: the content has already been checked; so only the occurrence of the fields must match

    def _authentication_tests(self):
        self._logout()

        # create and remove without be logged in
        reply = self.api_create_entry(0, self.order4, expected_result=200)
        self.id_order4 = self.get_primary_id(reply, self.db_spec)
        self.api_remove_entry(self.id_order4, expected_result=200)

        # create and remove as "normal user"
        user_pass = '{0}:{1}'.format(empl_api.employee1['username'], 'ff-pass')
        self.login(user_pass=user_pass)  # assertion if failed
        reply = self.api_create_entry(0, self.order4, expected_result=200)
        self.id_order4 = self.get_primary_id(reply, self.db_spec)
        self.api_remove_entry(self.id_order4, expected_result=200)
        self._logout()

        # create and remove as admin
        self.login_admin()  # assertion if failed
        reply = self.api_create_entry(0, self.order4, expected_result=200)
        self.id_order4 = self.get_primary_id(reply, self.db_spec)
        self.api_remove_entry(self.id_order4, expected_result=200)
        self._logout()

        self.query_size(expected_size=3, args={'predef_filter': 'projects-all'})


ord_api = OrderingsData()
