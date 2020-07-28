
def get_label_for_lang(lang, label_dict):
    if lang in label_dict:
        return label_dict[lang]
    if 'en' in label_dict:
        # return english as default text
        return label_dict['en']
    return '<undef>'


def get_primarykey_colname(table_name, db_spec):
    if table_name not in db_spec:
        return ''

    # expect just one primary key
    return [col_spec['name'] for col_spec in db_spec[table_name]['columns'] if col_spec['func'] == 'primarykey'][0]

