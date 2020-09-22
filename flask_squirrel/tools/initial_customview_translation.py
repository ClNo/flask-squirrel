import argparse
import json
import pprint

import jsbeautifier


def generate_translation(db_spec, translation_file):
    translation_dict = {}
    for table_name in db_spec:
        print(table_name)
        translation_dict[table_name] = {table_name: {'en': table_name}}
        table_spec = db_spec[table_name]['columns']
        # print(table_spec)
        for col_spec in table_spec:
            col_name = col_spec['name']
            if col_spec['func'] == 'primarykey':
                # the primary key is not used as entry field and does not need a translation
                translation_dict[table_name][col_name] = {'en': 'ID'}
            elif col_spec['func'] == 'foreignkey':
                translation_dict[table_name][col_name] = {'en': col_spec['reference']}
            elif col_spec['type'] == 'enum':
                translation_dict[table_name][col_name] = {'en': col_name}
                for enum in col_spec['type-details']:
                    translation_dict[table_name]['{0}.{1}'.format(col_name, enum)] = {'en': enum}
            else:
                translation_dict[table_name][col_name] = {'en': col_name}
        translation_dict[table_name]['_editor'] = {
            'table_multi': {'en': table_name}, 'table_single': {'en': table_name[:-1]}, 'article': {'en':  'a'}}

    translation_file.write(json.dumps(translation_dict, indent='  '))
    # translation_file.write(pprint.pformat(translation_dict, width=120, compact=True))
    # opts = jsbeautifier.default_options()
    # opts.indent_size = 2
    # translation_file.write(jsbeautifier.beautify(json.dumps(translation_dict), opts))


def generate_customview(db_spec, customview_file):
    customview_dict = {}
    for table_name in db_spec:
        if table_name == 'users':
            customview_dict[table_name] = {'_attributes': ['write_table_admin'],
                                           'username': {'_attributes': ['unique']},
                                           'credential_hash': {'_attributes': ['password']},
                                           '_predefined_filters': {}}
        else:
            customview_dict[table_name] = {'_attributes': [], '_predefined_filters': {}}
        
        table_spec = db_spec[table_name]['columns']
        for col_spec in table_spec:
            if col_spec['func'] == 'foreignkey':
                ref_table = col_spec['reference'].split('.')[0]
                customview_dict[table_name][col_spec['name']] = {'ref_text': guess_referenced_name(db_spec, ref_table)}

    customview_file.write(json.dumps(customview_dict, indent='  '))
    # customview_file.write(pprint.pformat(customview_dict, width=120, compact=True))


def guess_referenced_name(db_spec, ref_table_name):
    if ref_table_name not in db_spec:
        return []

    table_spec = db_spec[ref_table_name]['columns']

    # try to find a column with the string 'name' in it
    luckyshot_name_list = [col_spec for col_spec in table_spec if 'name' in col_spec['name']]
    if luckyshot_name_list:
        return ['{0}.{1}'.format(ref_table_name, col_spec['name']) for col_spec in luckyshot_name_list]

    # no column with string 'name' found, take the first two (?) string columns
    string_col_list = [col_spec for col_spec in table_spec if col_spec['type'] == 'string']
    if string_col_list:
        return ['{0}.{1}'.format(ref_table_name, col_spec['name']) for col_spec in string_col_list[:2]]  # max 2

    # else: no string column found -> do not return a column here
    return []


def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(description='Generate an initial customview and translation JSON file containing all DB fields')
    parser.add_argument('db_spec_file', help='DB specification JSON input file', type=argparse.FileType('r'))
    parser.add_argument('customview_file', help='initial empty customview spec file', type=argparse.FileType('w'))
    parser.add_argument('translation_file', help='initial empty translation file', type=argparse.FileType('w'))

    args = parser.parse_args()
    db_spec = json.load(args.db_spec_file)
    generate_translation(db_spec, args.translation_file)
    generate_customview(db_spec, args.customview_file)


if __name__ == '__main__':
    main()
