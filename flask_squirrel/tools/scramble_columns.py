import argparse
import json
import logging
from typing import Dict

import sqlalchemy
import sqlalchemy.ext.automap
from sqlalchemy import Table
from sqlalchemy.orm import sessionmaker

log = logging.getLogger('scramble_columns')
log.level = logging.DEBUG


def scramble(unscrambled):
    ''' 
    Scrambles the word(s) in unscrambled such that the first and last letter remain the same,
    but the inner letters are scrambled. Preserves the punctuation.
    See also: http://science.slashdot.org/story/03/09/15/2227256/can-you-raed-tihs
    '''
    import string, random, re
    splitter = re.compile(r'\s')
    # words = splitter.split(u''.join(ch for ch in unscrambled if ch not in set(string.punctuation)))
    words = splitter.split(u''.join(ch for ch in unscrambled))
    for word in words:
        if len(word) < 4: continue
        mid = list(word[1:-1])
        random.shuffle(mid)
        scrambled = u'%c%s%c' % (word[0], ''.join(mid), word[-1])
        unscrambled = unscrambled.replace(word, scrambled, 1)
    
    return unscrambled


def scramble_columns(table_columns, db_connect, db):
    collected_columns = {}
    for table_col in table_columns:
        tc_list = table_col.split('.')
        table_name = tc_list[0]
        col_name = tc_list[1]

        if table_name not in collected_columns:
            collected_columns[table_name] = []

        collected_columns[table_name].append(col_name)

    scrambled_tables = {}
    for table_name in collected_columns:
        rows = query_all_rows(table_name, collected_columns[table_name], db_connect, db)
        primary_key_name = db[table_name].primary_key.columns.keys()[0]  # this is only column name
        scrambled_items = []
        print(rows)
        for row in rows:
            update_row = {'primary_key_name': primary_key_name, 'primary_key_value': row[primary_key_name],
                          'update_col': {}}
            for col in collected_columns[table_name]:
                if row[col]:
                    update_row['update_col'][col] = scramble(row[col])

            if len(update_row['update_col']) > 0:
                scrambled_items.append(update_row)

        if scrambled_items:
            scrambled_tables[table_name] = scrambled_items

    print(scrambled_tables)
    return scrambled_tables


def query_all_rows(table_name, collected_columns, db_connect, db):
    table_obj: Table = db[table_name]
    sel = table_obj.select()  # whereclause=sqlalchemy.sql.text('`{0}`.`{1}`={2}'.format(table_name, primary_key_name, primary_key_value)))
    try:
        result = db_connect.execute(sel)
    except sqlalchemy.exc.IntegrityError as e:
        log.error('error in SQL query: {0}'.format(e))
        return None

    rows = result.fetchall()
    if rows:
        return rows

    return None


def update_table_columns(table_name, scrambled_items, db_connect, db):
    # Session = sessionmaker(bind=db_connect)
    # session = Session()

    for update_row in scrambled_items:
        table_obj: Table = db[table_name]
        filter_stm = sqlalchemy.sql.text('`{0}`.`{1}`={2}'.format(table_name, update_row['primary_key_name'], update_row['primary_key_value']))
        upd_cmd = table_obj.update().where(whereclause=filter_stm).values(update_row['update_col'])
        print(upd_cmd)

        try:
            # session.commit()
            db_connect.execute(upd_cmd)
        except sqlalchemy.exc.IntegrityError as e:
            log.error('error executing delete operation: {0}'.format(e))
            return

    print('Update of table {0} done'.format(table_name))


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Delete a row in a SQL table with all dependent rows in related '
                                                 'tables. All foreign keys will be checked recursively and shown in '
                                                 'the console output. If you want to delete all the rows in the '
                                                 'database you need to run it with the --force option.')
    parser.add_argument('-f', '--force', action='store_true', help='Execute the SQL delete commands, modify the database')
    parser.add_argument('sql_url', help='SQL database as URL like "sqlite:///./my-db.sqlite" (SQLAlchemy syntax)', type=str)
    parser.add_argument('scramble_columns', nargs='+', help='table_name.column_name specification which columns shall be scrambled', type=str)

    args = parser.parse_args()

    # print(args.scramble_columns)

    db_connect: sqlalchemy.Engine = sqlalchemy.create_engine(args.sql_url)
    db_meta: sqlalchemy.MetaData = sqlalchemy.MetaData()
    db = {}
    try:
        # now create SQLAlchemy ORM reflection objects (= read ORM from the existing DB)
        db_meta.reflect(bind=db_connect)
        for table_object in db_meta.sorted_tables:
            db[str(table_object)]: sqlalchemy.Table = table_object
            print(str(table_object))
        db_base: sqlalchemy.ext.automap.Base = sqlalchemy.ext.automap.automap_base(metadata=db_meta)
        db_base.prepare()
    except sqlalchemy.exc.SQLAlchemyError as e:
        print('SQL code:{0} message:{1}'.format(e.orig.args[0], e.orig.args[1]))
        exit(1)

    scrambled_tables = scramble_columns(args.scramble_columns, db_connect, db)
    # print_summary(scrambled_tables)

    if args.force:
        for table_name in scrambled_tables:
            update_table_columns(table_name, scrambled_tables[table_name], db_connect, db)

            # print()
            # print_sqlite_help()
    else:
        print('Note: not started in --force mode, nothing changed.')

    print()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
