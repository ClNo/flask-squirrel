# Documents: only show documents of running projects (via orderings):
#
# SELECT * FROM documents
# INNER JOIN orderings ON documents.idordering=orderings.idordering
# INNER JOIN projects ON orderings.idproject=projects.idproject AND projects.project_state='running';

# Orderings: only show orderings of running projects
#
# SELECT * FROM orderings
# INNER JOIN projects ON orderings.idproject=projects.idproject AND projects.project_state='running';
#                        ^^^^^^^^^ ^^^^^^^^^ ^^^^^^^^   ^^^^^^^     ^^^^^^^^^^^^^
#                        base_table base_col join_table join_col    and_condition
from typing import Optional

import logging
from flask.logging import default_handler

log = logging.getLogger('filter')
log.setLevel(logging.DEBUG)  # INFO
log.addHandler(default_handler)


class FilterSpec:

    def __init__(self, db_type: Optional[str]):
        self.db_type: Optional[str] = db_type

    @staticmethod
    def check_filter_spec(filter_spec, expected_keywords):
        found_keys = [key for key in filter_spec if key in expected_keywords]
        not_found_keys = [key for key in filter_spec if key not in expected_keywords]
        if (len(not_found_keys) == 1) and ('default' in not_found_keys):
            # accept the 'default' key; use it later
            not_found_keys = []
        return (len(found_keys) == len(expected_keywords)) and not not_found_keys


class JoinedFilterSpec(FilterSpec):
    # note: and_condition is the only condition until now. If there will be more they must be optional ('one-of-n').
    EXPECTED_KEYWORDS = ['base_table', 'base_column', 'join_table', 'join_column', 'and_condition']

    def __init__(self, filter_spec, db_type: Optional[str]):
        FilterSpec.__init__(self, db_type)
        self.filter_spec = filter_spec

    def is_default(self):
        return ('default' in self.filter_spec) and (self.filter_spec['default'])

    def generate_sql(self, filter_variables):
        # filter_variables: unused yet
        fs = self.filter_spec
        sql = 'INNER JOIN `{0}` ON `{1}`.`{2}`=`{0}`.`{3}` '.format(fs['join_table'], fs['base_table'],
                                                                    fs['base_column'], fs['join_column'])
        if 'and_condition' in fs:
            if type(fs['and_condition']) == str:
                sql += 'WHERE {0} '.format(fs['and_condition'])
            elif type(fs['and_condition']) == dict:
                if not self.db_type:
                    return '[ERROR: no database type specified #1]'
                if self.db_type not in fs['and_condition']:
                    return '[ERROR: no database type specified #2]'
                sql += 'WHERE {0} '.format(fs['and_condition'][self.db_type])

        return sql

    @staticmethod
    def check_create(filter_spec, db_type: Optional[str]):
        if FilterSpec.check_filter_spec(filter_spec, JoinedFilterSpec.EXPECTED_KEYWORDS):
            # joined filter found and correct
            return JoinedFilterSpec(filter_spec, db_type)
        return None


class SimpleSqlFilterSpec(FilterSpec):
    EXPECTED_KEYWORDS = ['sql_condition']

    def __init__(self, filter_spec, db_type: Optional[str]):
        FilterSpec.__init__(self, db_type)
        self.filter_spec = filter_spec

    def is_default(self):
        return ('default' in self.filter_spec) and (self.filter_spec['default'])

    def generate_sql(self, filter_variables):
        # filter_variables: unused yet
        return 'WHERE ' + self.filter_spec['sql_condition']

    @staticmethod
    def check_create(filter_spec, db_type: Optional[str]):
        if FilterSpec.check_filter_spec(filter_spec, SimpleSqlFilterSpec.EXPECTED_KEYWORDS):
            # joined filter found and correct
            return SimpleSqlFilterSpec(filter_spec, db_type)
        return None


class NoFilterSpec(FilterSpec):
    def __init__(self, filter_spec, db_type: Optional[str]):
        FilterSpec.__init__(self, db_type)
        self.filter_spec = filter_spec

    def is_default(self):
        return ('default' in self.filter_spec) and (self.filter_spec['default'])

    def generate_sql(self, filter_variables):
        # filter_variables: unused yet
        return ''  # this is an empty filter which means no results will be filtered => show all elements

    @staticmethod
    def check_create(filter_spec, db_type: Optional[str]):
        if (len(filter_spec) == 0) or (filter_spec is None) or \
                ((len(filter_spec) == 1) and ('default' in filter_spec)):
            return NoFilterSpec(filter_spec, db_type)
        return None


# this is more a filter handler / helper class than a fitler - rename?
class Filter:

    def __init__(self, filter_list=None, db_type: Optional[str] = None):
        self.db_type: Optional[str] = db_type
        self.filter_list = {}
        if filter_list:
            self.filter_list = filter_list.copy()

        self.direct_sql_command = None

    # def add_join(self, base_table, base_column, join_table, join_column, and_condition=None):
    #     self.join_list.append({'base_table': base_table, 'base_column': base_column,
    #                            'join_table': join_table, 'join_column': join_column,
    #                            'and_condition': and_condition})

    def add_filter_dict(self, filter_list):
        for fn in filter_list:
            filter_spec = filter_list[fn]
            filter_obj = JoinedFilterSpec.check_create(filter_spec, self.db_type)
            if filter_obj:
                # this is a join-filter e.g. only show orderings of active projects (= lookup in a second table)
                self.filter_list[fn] = filter_obj
                continue

            filter_obj = SimpleSqlFilterSpec.check_create(filter_spec, self.db_type)
            if filter_obj:
                # this is a simple SQL condition to filter e.g. one column
                self.filter_list[fn] = filter_obj
                continue

            filter_obj = NoFilterSpec.check_create(filter_spec, self.db_type)
            if filter_obj:
                # this is an empty filter which means no results will be filtered => show all elements
                self.filter_list[fn] = filter_obj
                continue

            log.error('no filter created for {0}, some keywords unknown: {1}'.format(fn, filter_spec))

    def set_sql_command(self, sql_command):
        self.direct_sql_command = sql_command

    def generate_statement(self, filter_name: Optional[str] = None, filter_variables: Optional[dict] = None):
        if self.direct_sql_command:
            return 'WHERE {0} '.format(self.direct_sql_command)

        # check if at least one filter exists
        if not self.filter_list:
            return None

        # use the first filter if there is exactly one filter in the list
        stored_filter: Optional[FilterSpec] = None
        if (not filter_name) and (len(self.filter_list) == 1):
            stored_filter = self.filter_list[0]

        if (not stored_filter) and (filter_name == 'default'):
            for fn in self.filter_list:
                if self.filter_list[fn].is_default():
                    stored_filter = self.filter_list[fn]
                    break

        # TODO: situation unclear; document it better
        if (not filter_name) and (len(self.filter_list) != 1):
            # no error any more (difficult for testing)! return '[ERROR: no filter name specified or empty]'
            return ''  # just return empty

        if not stored_filter:
            if filter_name not in self.filter_list:
                return '[ERROR: given filter name is wrong]'
            stored_filter = self.filter_list[filter_name]

        return stored_filter.generate_sql(filter_variables)
