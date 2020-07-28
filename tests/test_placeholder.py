from flask_squirrel.table.db_placeholder_parser import DbPlaceholderParser


def test_placeholder():
    # standalone test, so get the files itself
    customview_spec = {}
    translation_spec = {}
    db_spec = {}
    db_reflection = {}
    db_connect = None
    table_name = 'documents'
    linked_col = 'filename'
    source_row = {'name': 'Order 1', 'filename': 'upload_file_order.txt', 'type': 'order',
                  'filedate': '2019-09-04', 'idemployee_added': 2, 'idordering': 1,
                  'comment': 'delayed 123', 'state': 'assigned'}

    parser = DbPlaceholderParser(customview_spec, translation_spec, db_spec, db_reflection, db_connect)

    result, err_msg = parser.parse(table_name, linked_col, source_row, 'no/place.holder')
    assert result == 'no/place.holder', 'no placeholder did not work (result should be the same as the input)'

    result, err_msg = parser.parse(table_name, linked_col, source_row, '')
    assert result == '', 'empty placeholder did not work (result should be an empty string)'

    rename_rule = '{type}_{filedate}.{<file-ext>}'
    result, err_msg = parser.parse(table_name, linked_col, source_row, rename_rule)
    assert result == 'order_2019-09-04.txt', 'placeholder replacement error: {0}'.format(err_msg)

    # rename_rule = '{idordering.orderings.idproject.projects.name}/{type}_{filedate}.{<file-ext>}'
    # result, err_msg = parser.parse(table_name, linked_col, source_row, rename_rule)
    # assert result == '', 'empty placeholder did not work (result should be an empty string)'
