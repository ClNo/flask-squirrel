import argparse
import json

# import moz_sql_parser

# import sqlparse
# from sqlparse.sql import IdentifierList, Identifier, Parenthesis
# from sqlparse.tokens import Keyword, DML

import logging
import re

log = logging.getLogger('extractsql')
log.level = logging.DEBUG


def convert_type(sql_type_str, unsigned_int):
    if (sql_type_str == 'INT') and not unsigned_int:
        return 'int'
    if (sql_type_str == 'INT') and unsigned_int:
        return 'uint'
    if sql_type_str == 'ENUM':
        return 'enum'
    if sql_type_str == 'DATE':
        return 'date'
    if sql_type_str == 'DECIMAL':
        return 'decimal'
    if sql_type_str == 'VARCHAR':
        return 'string'
    raise Exception('SQL type {0} not defined'.format(sql_type_str))


def create_col_def(colstr):
    s = colstr.lstrip(' ')
    p0 = s.find(' ')
    col_spec = {'name': extract_identifier(s[:p0])}
    s = s[p0:].lstrip(' ')
    p0 = s.find(' ')
    p01 = s.find('(')
    p02 = s.find(')')
    type_details = None
    if p01 >= 0:
        type_str = s[:p01]
        type_details = s[p01+1:p02]
        detail_list = type_details.split(',')
        if len(detail_list) > 1:
            detail_list_extracted = []
            for det in detail_list:
                detail_list_extracted.append(extract_identifier(det))
            type_details = detail_list_extracted
        s = s[p02+1:].lstrip(' ')
    elif p0 >= 0:
        type_str = s[:p0]
        s = s[p0:].lstrip(' ')
    else:
        type_str = s

    col_spec['type'] = type_str
    col_spec['func'] = 'value'
    if type_details:
        col_spec['type-details'] = type_details

    unsigned_int = False
    if len(s) > 0:
        # handle flags
        if 'NOT NULL' in s:
            col_spec['not-null'] = True
        if 'AUTO_INCREMENT' in s:
            col_spec['auto-increment'] = True
        if 'UNSIGNED' in s:
            unsigned_int = True

    col_spec['type'] = convert_type(col_spec['type'], unsigned_int)

    return col_spec


def handle_primary_key(colstr, table_spec):
    p0 = colstr.find('(')
    p1 = colstr.find(')')
    col_name = extract_identifier(colstr[p0+1:p1])
    col_spec = [col for col in table_spec if col['name'] == col_name][0]
    col_spec['func'] = 'primarykey'


def handle_foreign_key(colstr, table_spec, foreign_key_name):
    # example:
    # - source: REFERENCES `company` (`idcompany`)
    # - found:  ['company', 'idcompany']
    names = re.findall('[`\'"]([a-zA-Z0-9]*)[`\'"]', colstr)
    col_name = names[1]
    col_spec = [col for col in table_spec if col['name'] == foreign_key_name][0]
    col_spec['func'] = 'foreignkey'

    ref_table_name = names[0]
    col_spec['reference'] = '.'.join([ref_table_name, col_name])
    # goal: "reference": "company.idcompany"


db_spec = {}


def extract_identifier(identstr):
    identstr = identstr.lstrip('(')
    identstr = identstr.lstrip(' ')
    identstr = identstr.lstrip('\'')
    identstr = identstr.lstrip('`')
    identstr = identstr.lstrip('"')
    identstr = identstr.rstrip(')')
    identstr = identstr.rstrip(' ')
    identstr = identstr.rstrip('\'')
    identstr = identstr.rstrip('`')
    identstr = identstr.rstrip('"')
    return identstr


def count_brace_level(line):
    return line.count('(') - line.count(')')


def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(description='Extract the SQL file and generate the JSON')
    parser.add_argument('sql_file', help='SQL input file', type=argparse.FileType('r'))
    parser.add_argument('db_spec_file', help='JSON output file for the DB specification', type=argparse.FileType('w'))

    # https://sqlparse.readthedocs.io/en/latest/analyzing/#sqlparse.sql.Statement

    args = parser.parse_args()
    # sql_parsed = sqlparse.parse(args.sql_file)

    print(args.sql_file)
    # sql_content = args.sql_file.read()

    table_name = ''
    foreign_key_name = ''
    brace_level = 0
    for line in args.sql_file:
        skip_line = False
        if line.startswith('--'):
            continue
        elif line.startswith('SET '):
            continue
        elif line.startswith('CREATE SCHEMA '):
            continue
        elif line.startswith('USE '):
            continue
        elif line.lstrip(' ') == '\n':
            continue
        elif line.startswith('CREATE TABLE '):
            pos_list = [line.find(c) for c in '"\'`' if line.find(c) >= 0]
            if len(pos_list) > 0:
                p0 = pos_list[0] + 1
                pos_list = [line.find(c, p0) for c in '"\'`' if line.find(c, p0) >= 0]
                p1 = pos_list[0]
                table_name = extract_identifier(line[p0:p1])
            else:
                p0 = line.find('.')
                p1 = line.find('(')
                table_name = extract_identifier(line[p0+1:p1])
            db_spec[table_name] = {'columns': []}
            skip_line = True

        if (brace_level == 1) and table_name and (not skip_line):
            if 'PRIMARY KEY' in line:
                # expect the column spec to be parsed already
                handle_primary_key(line, db_spec[table_name]['columns'])
            elif 'REFERENCES' in line:
                handle_foreign_key(line, db_spec[table_name]['columns'], foreign_key_name)
            elif 'INDEX' in line:
                pass  # do nothing
            elif 'CONSTRAINT' in line:
                pass  # do nothing
            elif 'NO ACTION' in line:
                pass  # do nothing
            elif 'FOREIGN KEY' in line:
                foreign_key_name = extract_identifier(line[line.find('(')+1:line.find(')')])
            else:
                col_spec = create_col_def(line)
                db_spec[table_name]['columns'].append(col_spec)

        brace_level += count_brace_level(line)
        if brace_level == 0:
            table_name = ''
            foreign_key_name = ''

    #tables = ', '.join(extract_tables(sql_content))

    #sql_dict = moz_sql_parser.parse(sql_content_stripped)
    #json.dumps(sql_dict, indent='  ')

    print('Tables: {0}'.format(''))
    print('--------------------------')
    print(db_spec)
    print('--------------------------')
    args.db_spec_file.write(json.dumps(db_spec, indent='\t'))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
