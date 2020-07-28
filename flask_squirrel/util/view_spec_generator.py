from flask_squirrel.table.dbutil import get_label_for_lang

from typing import Dict, Union, Tuple

import logging
from flask.logging import default_handler
log = logging.getLogger('view_spec_generator')
log.setLevel(logging.INFO)
log.addHandler(default_handler)


class ViewSpecGenerator:
    def __init__(self, customview_spec, translation_spec, db_spec):
        self.customview_spec = customview_spec
        self.translation_spec = translation_spec
        self.db_spec = db_spec
        self.current_lang = 'en'

    def generate_default_spec(self, table_name: str, lang: str):
        # lang is an ISO631 language code
        self.current_lang = lang

        view_spec = self._generate_resource_view_spec(table_name)
        log.debug('generated view spec for table {0} and lang {1}: {2}'.format(table_name, lang, view_spec))
        return view_spec

    def _generate_resource_view_spec(self, table_name: str) -> Dict[str, Union[str, list]]:
        # generate the resource view specification out of the 3 passed json files
        view_spec = {}
        if table_name in self.customview_spec:
            if '_attributes' in self.customview_spec[table_name]:
                if 'hidden' in self.customview_spec[table_name]['_attributes']:
                    # this is a table which is not show on the user interface as it used by the backend itself
                    return view_spec

        self._generate_table(table_name, view_spec)

        return view_spec

    def _generate_table(self, table_name: str, view_spec: Dict[str, Union[str, list]]) -> None:
        table_spec = None

        # check if the table is "virtual" - some business logic, but not a real table
        if table_name in self.customview_spec:
            if '_columns' in self.customview_spec[table_name]:
                table_spec = self.customview_spec[table_name]['_columns']

        if not table_spec:
            if table_name not in self.db_spec:
                log.error('The table named "{0}" is not specified in the database specification. JSON file not loaded?'
                          .format(table_name))
                return
            else:
                table_spec = self.db_spec[table_name]['columns']

        if table_name not in self.translation_spec:
            log.error('The table named "{0}" is not specified in the translation specification. JSON file not loaded?'
                      .format(table_name))
            return

        if table_name not in self.translation_spec[table_name]:
            log.error('The table name "{0}" itself is not translated. Append missing label!'
                      .format(table_name))
            return
        table_label = self.translation_spec[table_name][table_name]
        view_spec['label'] = get_label_for_lang(self.current_lang, table_label)

        # Note about editor-fields:
        # This is a specification of how a row of a table should be edited (some fields read only, some fields not-null
        # etc.).
        view_spec['editor-fields'] = []

        # Note about table-fields:
        # This is a specification of how to present the database content in a table.
        view_spec['table-fields'] = []

        for col_spec in table_spec:
            read_spec, edit_spec = self._generate_column(table_name, col_spec)
            if read_spec:
                view_spec['table-fields'].append(read_spec)
            if edit_spec:
                view_spec['editor-fields'].append(edit_spec)

    def _generate_column(self, table_name: str, col_spec: Dict[str, Union[None, str, bool, list, int]])\
            -> Tuple[Dict[str, Union[str, bool]], Dict[str, Union[str, bool]]]:
        col_name = col_spec['name']
        col_type = col_spec['type']
        col_func = None
        if 'func' in col_spec:
            col_func = col_spec['func']
        if col_func == 'primarykey':
            # do currently nothing with primary key
            return None, None

        title = col_name
        try:
            title = get_label_for_lang(self.current_lang, self.translation_spec[table_name][col_name])
        except Exception as e:
            log.error('No translation found for field {0} in table {1}'.format(col_name, table_name))

        name = '{0}.{1}'.format(table_name, col_name)
        if col_func == 'foreignkey':
            try:
                ref_text_list = self.customview_spec[table_name][col_name]['ref_text']
                name = ' '.join(ref_text_list)
            except Exception as e:
                log.error('No custom view specification found for foreign key {0} in table {1}'.format(col_name,
                                                                                                       table_name))

        field_view_read_spec = {'data': name, 'title': title}
        field_view_edit_spec = {'name': name, 'label': title}

        if ('not-null' in col_spec) and (col_spec['not-null'] is True):
            field_view_edit_spec['not-null'] = True

        if col_type == 'date':
            field_view_read_spec['type'] = 'date'
            field_view_edit_spec['type'] = 'datetime'
        elif col_type == 'decimal':
            field_view_read_spec['type'] = 'num-fmt'
            # unclear in editor: field_view_edit_spec['type'] = 'num-fmt'
        elif col_type == 'enum':
            field_view_edit_spec['type'] = 'select'
            # field_view_read_spec['type'] = 'string'
            field_view_read_spec['data'] = '{0}_{1}.name'.format(table_name, col_name)
        elif col_func == 'foreignkey':
            # ref_table_name, ref_id_name = col_spec['reference'].split('.')
            field_view_edit_spec['type'] = 'select'
            field_view_edit_spec['name'] = '{0}.{1}'.format(table_name, col_name)  # (ref_table_name, col_name)

        # handle fields as links
        link = None
        try:
            link = self.customview_spec[table_name][col_name]['filelink']
            # leaves if no link field found
            field_view_read_spec['link'] = True
        except TypeError:
            pass
        except KeyError:
            pass

        # handle readonly fields
        try:
            if 'editor_readonly' in self.customview_spec[table_name][col_name]['_attributes']:
                # use 'disabled' instead of readonly because it is used for date types as well as for strings etc.
                field_view_edit_spec['disabled'] = True
        except KeyError:
            pass

        try:
            if 'password' in self.customview_spec[table_name][col_name]['_attributes']:
                # use 'disabled' instead of readonly because it is used for date types as well as for strings etc.
                field_view_edit_spec['type'] = 'password'
                field_view_read_spec = None
        except KeyError:
            pass

        return field_view_read_spec, field_view_edit_spec
