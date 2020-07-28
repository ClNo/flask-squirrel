import copy
import datetime
from flask_restful import Resource
from flask import request, current_app
import json
import re

from flask_squirrel.table import linked_resource
from flask_squirrel.util.filter import Filter
from flask_squirrel.util.view_spec_generator import ViewSpecGenerator
from flask_squirrel.util import session_auth
from flask_squirrel.table.dbutil import get_label_for_lang, get_primarykey_colname
from flask_squirrel.util.session_auth import token_auth
from sqlalchemy import text

import logging
from flask.logging import default_handler
log = logging.getLogger('dbtable')
log.setLevel(logging.INFO)  # INFO or DEBUG?
log.addHandler(default_handler)


class DbTable(Resource):
    PASSWORD_REPLACEMENT = '----------'
    # method_decorators = {'post': [own_authenticate]}
    # method_decorators = {'post': [auth.login_required], 'put': [auth.login_required]}
    method_decorators = {
        'get': [token_auth.login_required],
        'post': [token_auth.login_required],
        'put': [token_auth.login_required]
    }

    def __init__(self, **kwargs):
        self.table_name = kwargs['table_name']
        log.info('Init resource handler for {0}...'.format(self.table_name))

        self.db_spec = current_app.config['db_spec']
        self.columns = current_app.config['db_spec'][self.table_name]['columns']
        self.db_connect = current_app.config['db_connect']
        self.customview_spec = current_app.config['customview_spec']
        self.translation_spec = current_app.config['translation_spec']
        self.current_lang = current_app.config['current_lang']
        self.view_spec_generator: ViewSpecGenerator = current_app.config['view_spec_generator']
        self.view_spec = None
        self.db_type: str = current_app.config['db_type']

        self.sql_query_columns = {}
        self.sql_query_columns_full = {}
        for table_nm in self.db_spec:
            # example:  'idemployee,abbr,firstname,lastname,state'
            self.sql_query_columns[table_nm] = ','.join([col['name'] for col in self.db_spec[table_nm]['columns']])
            self.sql_query_columns_full[table_nm] = ','.join(
                [table_nm + '.' + col['name'] for col in self.db_spec[table_nm]['columns']])

        # parse predefined filters for the main table (used in self._get_rows_main_table())
        self.predefined_filters_main = None
        if self.table_name in self.customview_spec:
            if '_predefined_filters' in self.customview_spec[self.table_name]:
                self.predefined_filters_main = self.customview_spec[self.table_name]['_predefined_filters']

        current_app.logger.addHandler(log)

        self._create_linked_resources()

    def _create_linked_resources(self):
        self.linked_resources = []

        if self.table_name not in self.customview_spec:
            # table not defined in customview_spec = no linked resource
            return

        for col in self.columns:
            col_name = col['name']
            if col_name in self.customview_spec[self.table_name]:
                col_spec = self.customview_spec[self.table_name][col_name]
                linked_res = linked_resource.link_resource_factory(self.table_name, col_name, col_spec, current_app.config)
                if linked_res:
                    self.linked_resources.append((col_name, linked_res))

    @staticmethod
    def _parse_request_args():
        args = {'lang': None, 'version': None, 'get_data': True, 'get_spec': None,
                'predef_filter': None, 'column_filter': None}

        try:
            # for PUT JSON args better use this: request_args = request.get_json(force=True)
            request_args = request.args
        except Exception as e:
            log.error('Request data is not JSON! mimetype:{0} type:{1} content:<{2}> exception:{3}'.
                      format(request.mimetype, type(request.data), request.data, e))
            return args

        # parse ISO631 language code
        if 'lang' in request_args:
            lang_tmp = request_args['lang']
            if re.match('^[a-z]{2}$', lang_tmp):
                log.debug('Resource view specification API request: passing language {0}'.format(lang_tmp))
                args['lang'] = lang_tmp

        if 'predef_filter' in request_args:
            args['predef_filter'] = request_args['predef_filter']

        if 'column_filter' in request_args:
            args['column_filter'] = {}
            for f in request_args['column_filter'].split('|'):
                filter_column, filter_value = f.split(':')
                if filter_value:
                    # filter value must be non-empty which means it's not null
                    args['column_filter'][filter_column] = filter_value

        if 'get' in request_args:
            if request_args['get'] == 'data':
                args['get_data'] = True
                args['get_spec'] = False
            elif request_args['get'] == 'spec':
                args['get_spec'] = True
                args['get_data'] = False
            elif request_args['get'] == 'data_spec':
                args['get_spec'] = True
                args['get_data'] = True

        return args

    def get(self):
        if current_app.config['db_fail']:
            # no DB connection, wrong config -> deny access
            return {'status': 'error', 'error': current_app.config['db_fail_err']}, 400

        args = self._parse_request_args()
        if 'lang' in args:
            self.current_lang = args['lang']

        if args['get_data']:
            # first get the current table for this object (self.table_name)
            rows_main_table = self._get_rows_main_table(sqlfilter=None, predef_filter_arg=args['predef_filter'],
                                                        column_filters=args['column_filter'])

            # generate the options / selection list which is only used for the editor
            dependant_rows = self._generate_options()
        else:
            rows_main_table = None
            dependant_rows = None

        translation = {}
        if args['get_spec']:
            # generate the filter list which can be used by a UI for selection lists etc.
            filter_list = self._generate_filters(self.table_name)
            editor_filter_list = self._generate_editor_filters(self.table_name)

            if self.table_name in self.translation_spec:
                if '_editor' in self.translation_spec[self.table_name]:
                    trans_list = self.translation_spec[self.table_name]['_editor']
                    for item in trans_list:
                        translation[item] = None
                        if self.current_lang in trans_list[item]:
                            translation[item] = trans_list[item][self.current_lang]
        else:
            filter_list = None
            editor_filter_list = None

        result_dict = {'data': rows_main_table, 'options': dependant_rows,
                       'filters': filter_list, 'editor-filters': editor_filter_list,
                       'translation': translation}

        if args['get_spec']:
            if not self.view_spec:
                # TODO: generate the spec again if self.current_lang has been changed!
                self.view_spec = self.view_spec_generator.generate_default_spec(self.table_name, self.current_lang)

            result_dict.update(self.view_spec)

        # log.info(rows_main_table)
        # UNUSED??? replaced_ref_table = self._replace_reference_fields(rows_main_table)
        # log.info(replaced_ref_table)
        return result_dict, 200

    def post(self):
        if current_app.config['db_fail']:
            # no DB connection, wrong config -> deny access
            return {'status': 'error', 'error': current_app.config['db_fail_err']}, 400

        # log.debug('request:')
        log.debug(request)
        in_data = None
        if request.form:
            in_data = dict(request.form)
        elif request.data:
            in_data = json.loads(request.data.decode('utf-8'))
        elif request.json:
            in_data = request.json
        log.debug('POST incoming request: {0}'.format(in_data))

        if not in_data:
            msg = 'Empty POST request makes no sense!'
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        # Format of in_data (example):
        # [('data[4][employees][firstname]', 'John'),
        #  ('data[4][employees][lastname]', 'Test'),
        #  ('action', 'edit'), ('data[4][employees][abbr]', 'JoTe5'),
        #  ('data[4][employees][state]', 'active')]
        request_data = {}  # json.loads(request.form)
        parameters = {}
        action = None
        for col_key in in_data:
            if 'action' in col_key:
                action = in_data[col_key]
                continue

            # col_key = 'data[row_10][users][first_name]'
            col_key_list = [k[:k.find(']')] for k in col_key.split('[')]
            if len(col_key_list) > 2:
                row_id = col_key_list[1]
                table_name = col_key_list[2]
            else:
                continue

            if row_id not in request_data:
                request_data[row_id] = {}
            if table_name not in request_data[row_id]:
                request_data[row_id][table_name] = {}

            if len(col_key_list) > 3:
                col_name = col_key_list[3]
            else:
                # do not accept smaller key lists; this could occur on remove operations but it doesn't matter
                try:
                    parameters[col_key] = in_data[col_key]
                except:
                    pass
                continue

            col_val = in_data[col_key]
            request_data[row_id][table_name][col_name] = col_val

        log.debug('action: {0} -> data: {1}'.format(action, request_data))
        ret_dict, status = self._handle_post_request(action, request_data, parameters)
        return ret_dict, status

    def _get_rows_main_table(self, sqlfilter, predef_filter_arg, column_filters):

        row_filter = None
        if sqlfilter:
            row_filter = Filter()
            row_filter.set_sql_command(sqlfilter)

        elif self.predefined_filters_main:
            row_filter = Filter(db_type=self.db_type)
            row_filter.add_filter_dict(self.predefined_filters_main)

        if row_filter:
            log.info('Query table \'{0}\' with filter: {1}'.format(self.table_name, row_filter.generate_statement(predef_filter_arg)))
        else:
            log.info('Query table \'{0}\''.format(self.table_name))

        rows_main_table = self._query_table(self.table_name, row_filter, predef_filter_arg, column_filters)

        # query dependant/linkes tables - used only for the viewer
        for row in rows_main_table:
            for col in self.columns:
                if ('func' in col) and (col['func'] == 'foreignkey'):
                    ref_table_name, ref_id_name = col['reference'].split('.')

                    # now get the foreign key out of the original query
                    ref_val = row[self.table_name][col['name']]

                    if ref_val is not None:
                        self._query_joined_table_to_row(row, ref_table_name, '{0}.{1} = {2}'.format(ref_table_name, ref_id_name, ref_val))
                    else:
                        # null value on joined / referenced table
                        self._add_null_reference(row, ref_table_name)

                # replace it later! elif is_password:
                #     row[self.table_name][col['name']] = self.PASSWORD_REPLACEMENT

                elif col['type'] == 'enum':
                    val = row[self.table_name][col['name']]
                    if val:
                        enum_spec = '{0}.{1}'.format(col['name'], val)  # col['type-details'][val])

                        # Note: the underscore naming is a bit strange but it makes sense as it is some kind of a reference
                        # not to an other table but to a list of possible selection items. Therefore a specific naming has
                        # been introduced here.
                        val = get_label_for_lang(self.current_lang, self.translation_spec[self.table_name][enum_spec])
                        row['{0}_{1}'.format(self.table_name, col['name'])] = {'name': val}
                    else:
                        # When does this situation happen? This could appear if an enum field has a null/None/empty value,
                        # which means that it was net set in the editor.
                        row['{0}_{1}'.format(self.table_name, col['name'])] = {'name': val}

            for col_name, linked in self.linked_resources:
                linked.modify_linked_entry(row)

        log.debug(rows_main_table)
        return rows_main_table

    def _generate_options(self, force_table_name=None, current_editor_filter=None):
        # generate the options / selection list which is only used for the editor
        dependant_rows = {}

        used_table_name = self.table_name
        if force_table_name:
            used_table_name = force_table_name

        for col in self.columns:
            if ('func' in col) and (col['func'] == 'foreignkey'):
                ref_table_name, ref_id_name = col['reference'].split('.')
                option_name = '{0}.{1}'.format(used_table_name, col['name'])  # (ref_table_name, col['name'])
                current_filter = None

                col_name = col['name']
                row_filter = None
                if col_name in self.customview_spec[used_table_name]:
                    if 'filter' in self.customview_spec[used_table_name][col_name]:
                        sql_command = self.customview_spec[used_table_name][col_name]['filter']
                        row_filter = Filter()
                        row_filter.set_sql_command(sql_command)

                # unclear: override row_filter if both are set?
                if current_editor_filter and (used_table_name in current_editor_filter) and\
                        (col['name'] in current_editor_filter[used_table_name]):
                    filter_dict = current_editor_filter[used_table_name][col['name']]
                    row_filter = Filter(db_type=self.db_type)
                    row_filter.add_filter_dict(filter_dict)
                    current_filter = current_editor_filter[used_table_name]['current_filter']

                dependant_rows[option_name] = self._build_options_list(self.table_name, col_name, ref_table_name,
                                                                       ref_id_name, row_filter, current_filter)
            elif col['type'] == 'enum':
                option_name = '{0}.{1}'.format(used_table_name, col['name'])
                dependant_rows[option_name] = self._build_enum_options_list(self.table_name, col['name'])
        return dependant_rows

    def _query_table(self, table_name, row_filter, predef_filter_arg=None, column_filters=None):
        conn = self.db_connect.connect()  # connect to database

        filterstr = ''
        if row_filter:
            filterstr = row_filter.generate_statement(predef_filter_arg)

        if column_filters:
            if len(filterstr) == 0:
                filterstr += ' WHERE '
                is_first = True
            else:
                is_first = False

            for column_name in column_filters:
                if not is_first:
                    filterstr += ' AND '
                else:
                    is_first = False
                filterstr += '{0}=\'{1}\''.format(column_name, column_filters[column_name])

        if filterstr:
            sql_str = 'SELECT {0} FROM {1} {2}'.format(self.sql_query_columns_full[table_name], table_name, filterstr)
        else:
            sql_str = 'SELECT {0} FROM {1}'.format(self.sql_query_columns_full[table_name], table_name)
        query = conn.execute(sql_str)
        query_rows = query.cursor.fetchall()
        col_name_list = self.sql_query_columns[table_name].split(',')
        data_dict_rows = []
        for row in query_rows:
            row_dict = self._format_row_for_json(table_name, col_name_list, row, True)
            data_dict_rows.append(row_dict)
        log.debug('SQL: {0} -> number of rows read: #{1}'.format(sql_str, len(query_rows)))

        return data_dict_rows

    def _format_row_for_json(self, table_name, col_name_list, row_from_db, handle_dt_row):
        row_dict = {table_name: {}}
        col_cnt = 0
        for val in row_from_db:
            col_name = col_name_list[col_cnt]
            col_spec = [col for col in self.db_spec[table_name]['columns'] if col['name'] == col_name][0]  # only one item expected!
            col_type = col_spec['type']
            col_func = col_spec['func']

            if (col_type == 'date') and (val is not None):
                if type(val) == str:
                    # this is a string, check if it's really a date
                    try:
                        datetime.datetime.strptime(val, '%Y-%m-%d').date()
                    except Exception as e:
                        log.error('Not an iso date string: \'{0}\': {1}'.format(val, e))
                        val = None
                else:
                    val = val.isoformat()

            elif (col_type == 'decimal') and (val is not None):  # <----- unclear!?
                # print(type(val)) <-- type: decimal.Decimal
                val = str(val)
            elif (col_type == 'enum') and val:
                pass
                # enum_spec = '{0}.{1}'.format(col_name, val)
                # try:
                #     global current_lang
                #     val = get_label_for_lang(current_lang, translation_spec[table_name][enum_spec])
                # except Exception as e:
                #     log.error('Error finding translation for enum {0} in table {1}: {2}'.format(enum_spec, table_name, e))

            if col_name in self.customview_spec[table_name]:
                col_spec = self.customview_spec[table_name][col_name]
                if '_attributes' in col_spec:
                    if 'password' in col_spec['_attributes']:
                        val = self.PASSWORD_REPLACEMENT

            row_dict[table_name][col_name] = val

            if handle_dt_row:
                if (self.table_name == table_name) and (col_func == 'primarykey'):
                    row_dict['DT_RowId'] = val

            col_cnt += 1
        return row_dict

    @staticmethod
    def _prepare_dict_for_json(src):
        for item in src:
            if type(src[item]) == datetime.date:
                src[item] = src[item].isoformat()

    def _replace_reference_fields(self, data_dict_rows):
        replaced_ref_rows = copy.deepcopy(data_dict_rows)
        rowcnt = 0
        for row in data_dict_rows:  # iterate through original, not copy
            for table_name in row:
                if type(row[table_name]) != dict:
                    # skip ID field
                    continue

                if table_name not in self.db_spec:
                    # this could be an enum
                    continue

                for col_name in row[table_name]:
                    col_spec = [col for col in self.db_spec[table_name]['columns'] if col['name'] == col_name]
                    # log.debug('replace ref field table:{0} col_name:{1} spec:{2}'.format(table_name, col_name, col_spec))
                    if col_spec:
                        col_spec = col_spec[0]  # only one item expected!
                    else:
                        continue
                    if col_spec['func'] == 'foreignkey':
                        # In case of a foreign key (= joined table) we link to a separate structure instead of passing
                        # the foreign key itself. We don't want to expose too much implementation details...
                        val = row[table_name][col_name]
                        ref_table_name, ref_id_name = col_spec['reference'].split('.')
            rowcnt += 0
        return replaced_ref_rows

    def _query_joined_table_to_row(self, to_row, table_name, sqlfilter):
        if sqlfilter is None:
            log.error('joined query cannot have an empty filter!')
            return

        conn = self.db_connect.connect()  # connect to database
        query = conn.execute('SELECT {0} FROM {1} WHERE {2}'.format(self.sql_query_columns[table_name], table_name, sqlfilter))
        query_result = query.cursor.fetchall()

        if len(query_result) != 1:
            log.error('joined query gives not a ONE single row but {0}'.format(len(query_result)))
            return
        row = query_result[0]
        to_row[table_name] = {}
        col_name_list = self.sql_query_columns[table_name].split(',')
        row_dict = self._format_row_for_json(table_name, col_name_list, row, False)
        to_row.update(row_dict)

    def _add_null_reference(self, row, ref_table_name):
        if ref_table_name not in self.db_spec:
            log.error('Error table {0} is not in self.db_spec!'.format(ref_table_name))
            return

        if ref_table_name in row:
            log.error('Error referenced table {0} is already existing in row: {1}'.format(ref_table_name, row))
            return

        row[ref_table_name] = {}

        for col_spec in self.db_spec[ref_table_name]['columns']:
            col_name = col_spec['name']
            # clear every field
            row[ref_table_name][col_name] = None

    def _build_options_list(self, table_name, col_name, ref_table_name, ref_id_name, row_filter=None, current_filter=None):
        try:
            ref_text_list = self.customview_spec[table_name][col_name]['ref_text']
        except Exception as e:
            log.error(
                'No custom view specification found for foreign key {0} in table {1}'.format(col_name, table_name))
            return []

        row_list = self._query_table(ref_table_name, row_filter, current_filter)
        option_list = []
        undefined_value = get_label_for_lang(self.current_lang, self.translation_spec[self.table_name][col_name])
        option_dict = {'label': '({0})'.format(undefined_value), 'value': None}
        option_list.append(option_dict)
        for row in row_list:
            field_label = []
            for ref_text in ref_text_list:
                ref_table_spec, column_to_print = ref_text.split('.')
                if ref_table_spec != ref_table_name:
                    log.error('Building option list - reference table mismatch: {0} vs. {1} table {2}'.format(ref_table_spec, ref_table_name, table_name))
                    return []

                field_label.append(row[ref_table_name][column_to_print])  # <----- THIS IS A FAILURE: [ref_table_name] <------
            option_dict = {'label': ' '.join(field_label), 'value': row[ref_table_name][ref_id_name]}  # <----- THIS IS A FAILURE: [ref_table_name] <------
            option_list.append(option_dict)

        return option_list

    def _build_enum_options_list(self, table_name, col_name):
        try:
            enum_spec_list = [col_spec['type-details'] for col_spec in self.db_spec[table_name]['columns']
                              if col_spec['name'] == col_name][0]
        except Exception as e:
            log.error('No enums found in table {0} for column {1}'.format(table_name, col_name))
            return []

        # now build a translated list
        option_list = []
        undefined_value = get_label_for_lang(self.current_lang, self.translation_spec[self.table_name][col_name])
        option_list.append({'label': '({0})'.format(undefined_value), 'value': None})

        for enum_name in enum_spec_list:
            key_name = '{0}.{1}'.format(col_name, enum_name)
            label = enum_name
            try:
                enum_label_list = self.translation_spec[table_name][key_name]
                label = enum_label_list[self.current_lang]
            except Exception as e:
                log.error('Error finding the translation for enum {0} in table {1}'.format(key_name, table_name))

            option_dict = {'label': label, 'value': enum_name}
            option_list.append(option_dict)

        return option_list

    def _generate_filters(self, table_name):
        filter_list = []
        if table_name not in self.customview_spec:
            return filter_list

        if ('_column_filters' in self.customview_spec[table_name]) and\
           (self.customview_spec[table_name]['_column_filters'] is None):
            for col_spec in self.db_spec[table_name]['columns']:
                if (col_spec['type'] == 'enum') or (col_spec['func'] == 'foreignkey'):
                    filter_list.append({'type': 'column', 'column': '{0}.{1}'.format(table_name, col_spec['name']), 'disable': True})

        if '_predefined_filters' not in self.customview_spec[table_name]:
            return filter_list

        filter_spec = self.customview_spec[table_name]['_predefined_filters']
        for filter_name in filter_spec:
            default = False
            if 'default' in filter_spec[filter_name]:
                default = filter_spec[filter_name]['default']

            trans_key_name = '{0}.{1}'.format('_predefined_filters', filter_name)
            translated_name = None
            try:
                translated_name = self.translation_spec[table_name][trans_key_name][self.current_lang]
            except Exception as e:
                log.error('Error finding the translation for filter {0} in table {1}'.format(filter_name, table_name))

            f = {'type': 'predefined', 'name': filter_name, 'default': default, 'translated_name': translated_name}
            filter_list.append(f)

        return filter_list

    def _generate_editor_filters(self, table_name):
        editor_filter_list = []
        if table_name not in self.customview_spec:
            return editor_filter_list
        if '_editor_filters' not in self.customview_spec[table_name]:
            return editor_filter_list

        filter_spec_col = self.customview_spec[table_name]['_editor_filters']
        for col_name in filter_spec_col:
            filter_spec = filter_spec_col[col_name]
            for filter_name in filter_spec:
                default = False
                if 'default' in filter_spec[filter_name]:
                    default = filter_spec[filter_name]['default']

                trans_key_name = '{0}.{1}'.format('_editor_filters', filter_name)
                translated_name = None
                try:
                    translated_name = self.translation_spec[table_name][trans_key_name][self.current_lang]
                except Exception as e:
                    log.error('Error finding the translation for editor filter {0} in table {1}'.format(filter_name, table_name))

                f = {'type': 'editor', 'field': col_name, 'name': filter_name, 'default': default, 'translated_name': translated_name}
                editor_filter_list.append(f)
        return editor_filter_list

    def _create_empty_row_dict(self, table_name):
        row_dict = {table_name: {}}
        col_name_list = self.sql_query_columns[table_name].split(',')
        for col_name in col_name_list:
            # we're creating an empty row dict
            row_dict[table_name][col_name] = None
            # DT_RowId is up to the caller
        return row_dict

    def _handle_post_request(self, action, request_data, parameters):
        # Go through each column and check if its available in the JSON request. If not, the field will be set to null
        # and it depends whether the SQL server accepts it or not (flag 'NN' = not null).

        if action == 'create':
            sql_cmd_pre = 'INSERT INTO {0}'.format(self.table_name)
            sql_cmd_post = ''

        elif action == 'edit':
            sql_cmd_pre = 'UPDATE {0}'.format(self.table_name)

        elif action == 'remove':
            sql_cmd_pre = 'DELETE FROM {0}'.format(self.table_name)

        else:
            msg = 'Action type {0} unknown!'.format(action)
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        primarykey_colname = get_primarykey_colname(self.table_name, self.db_spec)
        sql_cmd_values_str = ''

        for row_id in request_data:
            try:
                int(row_id)
            except ValueError:
                msg = 'Received ID is not a number: {0} (len:{1})'.format(row_id, len(row_id))
                log.error(msg)
                return {'status': 'error', 'error': msg}, 400

            # here, the whole SQL command will be generated step by step
            item = request_data[row_id]
            unique_query_col = None
            unique_query_val = None

            if (action == 'edit') or (action == 'remove'):
                sql_cmd_post = 'WHERE {0}={1}'.format(primarykey_colname, row_id, primarykey_colname)

            # 1. generate SQL values for writing
            if action != 'remove':
                # do nothing here on 'remove' (will generate errors)
                ret_dict, ret_code, sql_cmd_values_str, unique_query_col, unique_query_val =\
                    self._generate_create_edit_values(action, item, primarykey_colname)

                if ret_code != 200:
                    return ret_dict, ret_code

            # 2. generate SQL string
            sql_cmd = '{0} {1} {2}'.format(sql_cmd_pre, sql_cmd_values_str, sql_cmd_post)
            log.info(sql_cmd)

            # 3. optional check if a value has to be unique
            if unique_query_col and unique_query_val:
                ret_dict, ret_code = self._check_for_unique(action, primarykey_colname, row_id, unique_query_col, unique_query_val)
                if ret_code != 200:
                    return ret_dict, ret_code

            # 4. check if linked resource will accept this operation or not
            ret_dict, ret_code, previous_row = self._pre_check_linked_resource(action, item, row_id)
            if ret_code != 200:
                return ret_dict, ret_code

            # 5. execute SQL command
            ret_dict, ret_code, updated_row_ids, field_errors = self._execute_sql_post_request_item(action, item, sql_cmd, sql_cmd_post, row_id)
            if ret_code != 200:
                return ret_dict, ret_code

            # 6. handle linked resources
            # 'previous_row' is the row dict in the DB before it has been changed. This is used for modifying linked
            # resources (edit and delete).
            ret_dict, ret_code = self._execute_linked_resource_action(action, item, row_id, previous_row)
            if ret_code != 200:
                # TODO: revert the last SQL statement on errors!
                return ret_dict, ret_code

        # now read the changed rows and pass it back to the table
        sqlfilter = ''
        for row_id in updated_row_ids:
            if sqlfilter:
                sqlfilter += ' OR '
            sqlfilter += '({0}={1})'.format(primarykey_colname, row_id)
        # update all rows which have been updated, so do not apply any predefined filters in this request
        rows_main_table = self._get_rows_main_table(sqlfilter=sqlfilter, predef_filter_arg=None, column_filters=None)

        return {'status': 'success', 'data': rows_main_table, 'fieldErrors': field_errors}, 200

    def _generate_create_edit_values(self, action, item, primarykey_colname):
        sql_cmd_values_str = ''
        commit_values = []
        set_values = []

        unique_query_col = None
        unique_query_val = None

        # first check if every field in the request is known as a column
        for col_name in item[self.table_name]:
            col_list = [col['name'] for col in self.columns if col['name'] == col_name]
            if len(col_list) != 1:
                msg = 'SQL insert/update failed: request field {0} is not known in the table {1}'. \
                    format(col_name, self.table_name)
                log.error(msg)
                return {'status': 'error', 'error': msg}, 400, None, None, None

        for col in self.columns:
            col_name = col['name']

            is_password = False
            if self.table_name in self.customview_spec:
                if col['name'] in self.customview_spec[self.table_name]:
                    col_spec = self.customview_spec[self.table_name][col['name']]
                    if '_attributes' in col_spec:
                        if 'password' in col_spec['_attributes']:
                            is_password = True
                        if 'unique' in col_spec['_attributes']:
                            unique_query_col = col['name']
                            if col['name'] in item[self.table_name]:
                                unique_query_val = item[self.table_name][col['name']]
                            # else: should fail later if it's empty

            if col_name == primarykey_colname:
                # skip primary key; already handled
                if action == 'create':
                    # null means: take the next available ID (expects autoincrement)
                    commit_values.append('null')
                    set_values.append('{0}=null'.format(col_name))
                elif action == 'edit':
                    pass

            elif col_name in item[self.table_name]:
                val = item[self.table_name][col_name]
                if val is not None:
                    if is_password:
                        # for new entries: calc a hash out of a clear text password
                        commit_values.append('\'' + session_auth.User.calc_hash_password(val) + '\'')
                        # for changed entries: check first if the password has been changed
                        if val != self.PASSWORD_REPLACEMENT:
                            # yes, PW has changed so calc a hash for this new plain text PW
                            set_values.append(
                                '{0}=\'{1}\''.format(col_name, session_auth.User.calc_hash_password(val)))
                        # else: do not modify the PW
                    elif type(val) == str:
                        val = val.replace('\'', '').replace('"', '').replace(';', '').replace('`', '')
                        commit_values.append('\'' + val + '\'')
                        set_values.append('{0}=\'{1}\''.format(col_name, val))
                    elif type(val) == int:
                        commit_values.append('\'' + str(val) + '\'')
                        set_values.append('{0}=\'{1}\''.format(col_name, val))
                    else:
                        log.error('Unknown data type in value \'{0}\''.format(val))
                else:  # None or empty
                    commit_values.append('null')
                    set_values.append('{0}=null'.format(col_name))

            elif col['func'] == 'foreignkey':
                ref_table_name, ref_id_name = col['reference'].split('.')
                val = None
                try:
                    val = item[ref_table_name][col_name]
                except ValueError:
                    pass

                if val:
                    commit_values.append('\'' + val + '\'')
                    set_values.append('{0}=\'{1}\''.format(col_name, val))
                else:
                    commit_values.append('null')
                    set_values.append('{0}=null'.format(col_name))

            else:
                # not set in request -> check what happens if set to Null...
                commit_values.append('null')
                set_values.append('{0}=null'.format(col_name))

        if action == 'create':
            sql_cmd_values_str = 'VALUES (' + ','.join(commit_values) + ')'

        elif action == 'edit':
            sql_cmd_values_str = 'SET ' + ', '.join(set_values)

        return {}, 200, sql_cmd_values_str, unique_query_col, unique_query_val

    def _check_for_unique(self, action, primarykey_colname, row_id, unique_query_col, unique_query_val):
        try:
            conn = self.db_connect.connect()

            # first check if the column value already exists
            sql_cmd_unique_query = 'SELECT * FROM {0} WHERE {0}.{1}="{2}"'.format(self.table_name,
                                                                                  unique_query_col,
                                                                                  unique_query_val)
            result = conn.execute(text(sql_cmd_unique_query))
            for entry in result:
                # for loop: only way to find out if one row has been found or not!
                if (action == 'edit') and (str(entry[primarykey_colname]) == row_id):
                    # what's that? it's allowed on edit operations to use the same unique values if the primary
                    # ID does not change
                    pass
                else:
                    return {'status': 'error',
                            'error': '{0}={1} already exists'.format(unique_query_col, unique_query_val)}, 400

        except Exception as e:
            log.error('SQL insert failed: {0}'.format(e))
            return {'status': 'error', 'error': str(e)}, 400

        return {}, 200

    def _pre_check_linked_resource(self, action, item, row_id):
        field_errors = []
        previous_row = None
        for col_name, linked in self.linked_resources:
            if action == 'create':
                succeed, msg, previous_row = linked.create_check(item[self.table_name])
                # there is no previous row in the 'create' operation
                if not succeed:
                    field_errors.append({'name': '{0}.{1}'.format(self.table_name, col_name), 'status': msg})
                    return {'status': 'error', 'error': msg, 'fieldErrors': field_errors}, 400, previous_row

            elif action == 'edit':
                succeed, msg, previous_row = linked.edit_check(row_id, item[self.table_name])
                if not succeed:
                    field_errors.append({'name': '{0}.{1}'.format(self.table_name, col_name), 'status': msg})
                    return {'status': 'error', 'error': msg, 'fieldErrors': field_errors}, 400, previous_row

            elif action == 'remove':
                succeed, msg, previous_row = linked.delete_check(row_id)
                if not succeed:
                    field_errors.append({'name': '{0}.{1}'.format(self.table_name, col_name), 'status': msg})
                    return {'status': 'error', 'error': msg, 'fieldErrors': field_errors}, 400, previous_row

        return {}, 200, previous_row

    def _execute_sql_post_request_item(self, action, item, sql_cmd, sql_cmd_post, row_id):
        updated_row_ids = []
        field_errors = []

        try:
            conn = self.db_connect.connect()
            result = conn.execute(text(sql_cmd).execution_options(autocommit=True))
        except Exception as e:
            log.error('SQL insert failed: {0}'.format(e))
            return {'status': 'error', 'error': str(e)}, 400, None, None

        log.debug('rowcount:{0} in condition {1}'.format(result.rowcount, sql_cmd_post))
        if action == 'create':
            log.debug('created new row with the primarykey {0}'.format(result.lastrowid))
            updated_row_ids.append(result.lastrowid)

        elif action == 'edit':
            if result.rowcount == 0:
                msg = 'no row matched {0}'.format(sql_cmd_post)
                log.error('SQL update failed: no row matched {0}'.format(msg))
                return {'status': 'error', 'error': msg}, 400, None, None
            log.info('updated row with the primarykey {0}'.format(row_id))
            updated_row_ids.append(row_id)

        return {}, 200, updated_row_ids, field_errors

    def _execute_linked_resource_action(self, action, item, row_id, previous_row):
        field_errors = []
        for col_name, linked in self.linked_resources:
            if action == 'create':
                succeed, msg = linked.create(item[self.table_name])  # no previous_row in create action
                # there is no previous row in the 'create' operation
                if not succeed:
                    field_errors.append({'name': '{0}.{1}'.format(self.table_name, col_name), 'status': msg})
                    return {'status': 'error', 'error': msg, 'fieldErrors': field_errors}, 400

            elif action == 'edit':
                succeed, msg = linked.edit(item[self.table_name], previous_row)
                if not succeed:
                    field_errors.append({'name': '{0}.{1}'.format(self.table_name, col_name), 'status': msg})
                    return {'status': 'error', 'error': msg, 'fieldErrors': field_errors}, 400

            elif action == 'remove':
                succeed, msg = linked.delete(row_id, previous_row)
                if not succeed:
                    field_errors.append({'name': '{0}.{1}'.format(self.table_name, col_name), 'status': msg})
                    return {'status': 'error', 'error': msg, 'fieldErrors': field_errors}, 400

        return {}, 200

    @staticmethod
    def _merge_options_into_editor(forced_table_name, options, editor_fields):
        # For the standalone editor: copy the options from the separate field directly into the edit-fields list
        for option in options:
            editor_field = [field for field in editor_fields if field['name'] == option]
            if editor_field:
                editor_field[0]['options'] = options[option]
