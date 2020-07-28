import re
import argparse


def mysql_to_sqlite(sql_input_filename, sqlite_output_filename):

    with open(sql_input_filename, 'r', encoding='utf8') as f:
        lines = list(f)

    out_lines = []
    schema = None
    engine = 'ENGINE = InnoDB'

    for line in lines:
        cmp_line: str = line.upper().strip()
        if cmp_line.startswith('SET '):
            continue
        if cmp_line.startswith('INDEX '):
            continue
        if 'CREATE SCHEMA' in cmp_line:
            continue
        if cmp_line.startswith('USE ') and cmp_line.endswith(';'):
            schema = line.strip()[3:-1].strip()
            continue

        out_line: str = line

        if schema and schema in line:
            out_line = line.replace('{0}.'.format(schema), '')
        if engine in line:
            out_line = line.replace(engine, '')

        # SQLite doesn't like the MYSQL's auto increment syntax; primary keys are always auto incremented
        # expect every auto increment to be a primary key! otherwise it's a problem...
        if 'AUTO_INCREMENT' in out_line.upper():
            pos1 = out_line.upper().index('INT')
            pos2 = out_line.index(',', pos1)
            out_line = out_line[0:pos1] + 'INTEGER PRIMARY KEY' + out_line[pos2:]

        # remove primary key "original" line as it is declared above; take care about the comma here
        if 'PRIMARY KEY' in cmp_line:
            pos1 = out_line.upper().index('PRIMARY KEY')
            pos2 = out_line.index(')', pos1)
            out_line = out_line[pos2+1:]

            # now: remove the comma in the previous line!
            pos1 = out_lines[-1].rindex(',')
            if pos1:
                out_lines[-1] = out_lines[-1][:pos1]

        # remove enums which are not supported by SQlite
        out_line = re.sub(r'(.*)(enum|ENUM\(.*\))(.*)', r'\1VARCHAR\3', out_line)

        if out_line:
            out_lines.append(out_line)

    with open(sqlite_output_filename, 'w') as f:
        f.writelines(out_lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert a MySQL Workbench SQL file to a SQLite syntax file. Note thath the parsing of the input file is very raw.')
    parser.add_argument("in_filename", help='MySQL Workbench Export SQL input file (no DROP statements expected)')
    parser.add_argument("out_filename", help='SQLite syntax SQL output file')
    args = parser.parse_args()

    mysql_to_sqlite(args.in_filename, args.out_filename)
