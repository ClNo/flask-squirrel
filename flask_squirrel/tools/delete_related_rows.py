import argparse
import json
import logging
from typing import Dict

import sqlalchemy
import sqlalchemy.ext.automap
from sqlalchemy import Table

log = logging.getLogger('delete_related_rows')
log.level = logging.DEBUG


def get_all_dependencies(args: argparse.ArgumentParser, db: Dict[str, sqlalchemy.Table]):
    if args.table_name not in db:
        log.error('Error table {0} not found in db {1}'.format(args.table_name, args.sql_url))
        exit(2)

    if args.table_name not in db:
        log.error('Error table {0} not found in db {1}'.format(args.table_name, args.sql_url))
        exit(2)

    # this is the entry point: get the row of the first table (from the command argument) and search dependencies for it
    source_column = '{0}.{1}'.format(args.table_name, args.primary_key_name)
    dependency_table = get_table_dependency(source_column, db)
    all_dependencies = dependency_table
    scanned_dependencies = [source_column]

    recursive_dependency_scan(all_dependencies, dependency_table, scanned_dependencies, db)

    return all_dependencies


def recursive_dependency_scan(all_dependencies, dependency_table, scanned_dependencies, db: Dict[str, sqlalchemy.Table]):
    has_new_deps = False
    for dependency in dependency_table:
        next_dependency = dependency['primary_key']
        if next_dependency in scanned_dependencies:
            continue

        table_deps = get_table_dependency(next_dependency, db)
        if table_deps:
            for dep in table_deps:
                if dep not in all_dependencies:
                    all_dependencies.append(dep)
            has_new_deps = True

        scanned_dependencies.append(next_dependency)

    if has_new_deps:
        recursive_dependency_scan(all_dependencies, dependency_table, scanned_dependencies, db)


def get_table_dependency(source_column, db: Dict[str, sqlalchemy.Table]):
    dependency_table = []
    # print('\n* scanning for usage of {0}'.format(source_column))

    for table_name in db:
        table_deps = {'name': table_name}
        for constraint in db[table_name].constraints:
            if not constraint.columns:
                pass

            elif type(constraint) == sqlalchemy.PrimaryKeyConstraint:
                primary_key = next(iter(constraint.columns))
                primary_key_name = str(primary_key)
                # print('Table {0} - primary key found: {1}'.format(table_name, primary_key_name))
                table_deps['primary_key'] = primary_key_name

            else:
                for constraint_element in constraint:
                    if constraint_element.foreign_keys:
                        foreign_key = next(iter(constraint_element.foreign_keys))
                        foreign_key_name = str(foreign_key.column)
                        if foreign_key_name == source_column:
                            # print('Found constraint in table/column {0} -> {1}'.format(str(constraint_element), source_column))
                            table_deps['foreign_key'] = foreign_key_name
                            if 'linked_column' not in table_deps:
                                table_deps['linked_column'] = []
                            table_deps['linked_column'].append(str(constraint_element))

        if ('primary_key' in table_deps) and ('foreign_key' in table_deps):
            dependency_table.append(table_deps)

        # print('* table {0} checked: {1}'.format(table_name, table_deps))

    print('--- The table {0} is used in the following tables (= linked foreign keys) ---'.format(source_column))
    print(json.dumps(dependency_table))
    print()
    return dependency_table


def query_all(args: argparse.ArgumentParser, db_connect, db_meta, db_base, db, all_dependencies):
    all_entries_to_delete = []

    rows = query_single(args.table_name, args.primary_key_name, args.primary_key_value, db_connect, db_meta,
                        db_base, db)

    if not rows:
        log.error('Error no row with primary key {0}.{1}={2} found!'.format(args.table_name, args.primary_key_name, args.primary_key_value))
        return None

    for row in rows:
        all_entries_to_delete.append({'table': args.table_name, 'primary_key': args.primary_key_name, 'id': row[args.primary_key_name]})

    for dependency in all_dependencies:
        for linked_column in dependency['linked_column']:
            # print('Query table {0}: {1}'.format(dependency['name'], dependency['primary_key']))
            linked_table_name = dependency['foreign_key'][:dependency['foreign_key'].index('.')]
            query_key_id_list = [entry['id'] for entry in all_entries_to_delete if entry['table'] == linked_table_name]
            if not query_key_id_list:
                continue
            for query_key_id in query_key_id_list:
                linked_col_name = linked_column[linked_column.index('.')+1:]
                dep_rows = query_single(dependency['name'], linked_col_name, query_key_id, db_connect, db_meta, db_base, db)
                if dep_rows:
                    for row in dep_rows:
                        primary_key_name = dependency['primary_key'][dependency['primary_key'].index('.')+1:]
                        is_existing = [entry for entry in all_entries_to_delete if entry['table'] == dependency['name'] and entry['id'] == row[primary_key_name]]
                        if not is_existing:
                            all_entries_to_delete.append({'table': dependency['name'], 'primary_key': primary_key_name, 'id': row[primary_key_name]})
                # print(dep_rows)

    return all_entries_to_delete


def query_single(table_name, primary_key_name, primary_key_value, db_connect, db_meta, db_base, db):
    table_obj: Table = db[table_name]
    sel = table_obj.select(whereclause=sqlalchemy.sql.text('`{0}`.`{1}`={2}'.format(table_name, primary_key_name, primary_key_value)))
    try:
        result = db_connect.execute(sel)
    except sqlalchemy.exc.IntegrityError as e:
        log.error('error in SQL query: {0}'.format(e))
        return None

    row = result.fetchall()
    if row:
        return row

    return None


def calc_summary(all_entries_to_delete):
    to_delete_summary = {}
    if not all_entries_to_delete:
        return to_delete_summary

    for entry in all_entries_to_delete:
        if entry['table'] not in to_delete_summary:
            to_delete_summary[entry['table']] = []
        to_delete_summary[entry['table']].append(entry['id'])

    return to_delete_summary


def print_summary(to_delete_summary):
    if len(to_delete_summary) == 0:
        print('No rows and dependencies found to be deleted')
        return

    print('Rows and dependent entries of different tables to be deleted:')

    for table in to_delete_summary:
        print('--- Table: {0} ---'.format(table))
        print(', '.join([str(rid) for rid in to_delete_summary[table]]))
        print()


def print_sqlite_help():
    print('Now do a manual database check! For SQlite do the following commands:')
    print('- integrity check: PRAGMA integrity_check')
    print('- foreign key check: PRAGMA foreign_key_check')
    print()
    print('The database size can be reduced now: VACUUM')


def do_delete_all(all_entries_to_delete, db_connect, db):
    print('Delete all {0} entries...'.format(len(all_entries_to_delete)))

    # Note: the SQL statements could be combined within a session but this would need to use the ORM layer. The ORM
    # cannot be used here as everything is read from the automapped db structure. So maybe an other solution can be
    # introduced in future ...

    # unclear: do all the delete operations from the end to the beginning?
    for entry in all_entries_to_delete:
        table_obj: Table = db[entry['table']]
        filter_stm = sqlalchemy.sql.text('`{0}`.`{1}`={2}'.format(entry['table'], entry['primary_key'], entry['id']))
        del_cmd = table_obj.delete().where(whereclause=filter_stm)

        try:
            # session.commit()
            db_connect.execute(del_cmd)
        except sqlalchemy.exc.IntegrityError as e:
            log.error('error executing delete operation: {0}'.format(e))
            return

    print('Deletion done.')


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Delete a row in a SQL table with all dependent rows in related '
                                                 'tables. All foreign keys will be checked recursively and shown in '
                                                 'the console output. If you want to delete all the rows in the '
                                                 'database you need to run it with the --force option.')
    parser.add_argument('-f', '--force', action='store_true', help='Execute the SQL delete commands, modify the database')
    parser.add_argument('sql_url', help='SQL database as URL like "sqlite:///./my-db.sqlite" (SQLAlchemy syntax)', type=str)
    parser.add_argument('table_name', help='Table name where a row will be deleted', type=str)
    parser.add_argument('primary_key_name', help='Primary key name of the table you want to delete a row', type=str)
    parser.add_argument('primary_key_value', help='Primary key value (= row ID) to specify the row to be deleted', type=str)

    args = parser.parse_args()

    db_connect: sqlalchemy.Engine = sqlalchemy.create_engine(args.sql_url)
    db_meta: sqlalchemy.MetaData = sqlalchemy.MetaData()
    db = {}
    try:
        # now create SQLAlchemy ORM reflection objects (= read ORM from the existing DB)
        db_meta.reflect(bind=db_connect)
        for table_object in db_meta.sorted_tables:
            db[str(table_object)]: sqlalchemy.Table = table_object
            # print(str(table_object))
        db_base: sqlalchemy.ext.automap.Base = sqlalchemy.ext.automap.automap_base(metadata=db_meta)
        db_base.prepare()
    except sqlalchemy.exc.SQLAlchemyError as e:
        print('SQL code:{0} message:{1}'.format(e.orig.args[0], e.orig.args[1]))
        exit(1)

    all_dependencies = get_all_dependencies(args, db)
    all_entries_to_delete = query_all(args, db_connect, db_meta, db_base, db, all_dependencies)
    # resulting list for instance:
    # [{'table': 'company', 'primary_key': 'idcompany', 'id': 8}, {'table': 'companyaddress',
    # 'primary_key': 'idcompanyaddress', 'id': 5}, {'table': 'companycontact', 'primary_key':
    # 'idcompanycontact', 'id': 5}, ....
    to_delete_summary = calc_summary(all_entries_to_delete)

    print()
    print_summary(to_delete_summary)

    if args.force:
        if all_entries_to_delete and (len(all_entries_to_delete) > 0):
            do_delete_all(all_entries_to_delete, db_connect, db)
            print()
            print_sqlite_help()
    else:
        print('Note: not started in --force mode, nothing changed.')

    print()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
