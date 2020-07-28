import os

import sqlalchemy
from sqlalchemy import Table

from flask_squirrel.table.dbutil import get_primarykey_colname


class DbPlaceholderParser:
    def __init__(self, customview_spec, translation_spec, db_spec, db_reflection, db_connect):
        self.customview_spec = customview_spec
        self.translation_spec = translation_spec
        self.db_spec = db_spec
        self.db_reflection = db_reflection
        self.db_connect = db_connect

    def parse(self, table_name: str, linked_col: str, source_row: dict, rename_rule: str):
        result = ''
        # example: rename_rule = '{idordering.orderings.idproject.projects.name}/{type}_{filedate}.{ext}'
        pos1: int = rename_rule.find('{')
        last_pos = 0
        while pos1 >= 0:
            # first copy the character between last_pos and the placeholder
            result += rename_rule[last_pos:pos1]

            pos2: int = rename_rule.find('}', pos1+1)
            if pos2 < 1:
                return None, 'No closing bracket for opening bracket at position {0}'.format(pos1)

            expr: str = rename_rule[(pos1+1):pos2]
            replaced_str, err_msg = self._replace_expr(table_name, linked_col, source_row, expr)
            if not replaced_str:
                return None, err_msg
            result += replaced_str

            last_pos = pos2 + 1
            pos1 = rename_rule.find('{', last_pos)

        result += rename_rule[last_pos:]

        return result, None

    def _replace_expr(self, table_name: str, linked_col: str, source_row: dict, expr: str):
        elem_list = expr.split('.')
        if len(elem_list) == 0:
            return None, 'empty brackets'

        replaced = ''
        reference_id = None

        current_row = source_row
        while len(elem_list) > 0:
            elem = elem_list[0]
            remaining_elem = len(elem_list) - 1

            if elem == '<file-ext>':
                if linked_col not in source_row:
                    return None, 'trying to extract file extension out of column \'{0}\' but it\'s not found: {1}'.\
                        format(linked_col, current_row)
                filename, file_extension = os.path.splitext(source_row[linked_col])
                if len(file_extension) == 0:
                    return None, 'trying to extract file extension out of string \'{0}\' but it\'s empty: {1}'.\
                        format(linked_col, current_row)
                if file_extension[0] == '.':
                    file_extension = file_extension[1:]
                replaced += file_extension

            elif (remaining_elem > 0) and (elem in current_row):
                # this is a reference primary key to an other table -> store the ID/key and use it the next time
                reference_id = current_row[elem]

            elif reference_id and (elem in self.db_spec):
                # an ID/primary key has been set previously and now a table name has been set
                table_name = elem
                primarykey_name = get_primarykey_colname(table_name, self.db_spec)
                table: Table = self.db_reflection[table_name]
                sel = table.select(whereclause=sqlalchemy.sql.text('{0}.{1}={2}'.format(table_name, primarykey_name, reference_id)))
                try:
                    result = self.db_connect.execute(sel)
                except sqlalchemy.exc.IntegrityError as e:
                    return None,  'SQL error reading table \'{0}\' where \'{1}={2}\': {0}'.format(table_name, primarykey_name, reference_id, e)

                row = result.fetchone()
                if not row:
                    return None, 'SQL error reading table \'{0}\' where \'{1}={2}\' (empty results)'.\
                                 format(table_name, primarykey_name, reference_id)
                current_row = row

            elif elem not in current_row:
                return None, 'element \'{0}\' not found in dict: {1}'.format(elem, current_row)

            else:
                # the 'elem' seems to be something directly in the row...
                replaced += str(current_row[elem])

            # this element has been used; continue with remaining elements
            del elem_list[0]  # ok, handled, do next

        return replaced, None
