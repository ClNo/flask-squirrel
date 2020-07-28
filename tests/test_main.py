# import json
from werkzeug import test


def test_ordermanagement_full(client: test.Client):
    """Test resource spec."""

    from tests import api_tools
    api_tools.test_client = client

    from tests.api_translation import translation_api
    translation_api.translation_test()

    from tests.api_employees import empl_api
    empl_api.initial_data()
    empl_api.extended_tests()

    from tests.api_suppliers import suppl_api
    suppl_api.initial_data()

    from tests.api_projects import proj_api
    proj_api.initial_data()

    from tests.api_orderings import ord_api
    ord_api.initial_data()
    ord_api.verbose_content_check()

    from tests.api_upload import upload_file
    upload_file.upload_test()

    from tests.api_documents import doc_api
    doc_api.initial_data()

    # from tests.api_new_ordering_doc import new_ordering_doc_data
    # new_ordering_doc_data.initial_data()
    #
    # from tests.api_orderinvoices import ordinv_api
    # ordinv_api.check_invoices()

    # print(reply)

# New: http://localhost:8080/ordermanagement-api/employees  POST
# action	create
# data[0][employees][abbr]	FF
# data[0][employees][firstname]	Fred
# data[0][employees][lastname]	Fisch
# data[0][employees][state]	active

# Reply
# {"status": "success", "data": [{"employees": {"idemployee": 7, "abbr": "FF", "firstname": "Fred", "lastname": "Fisch", "state": "active"},
# "DT_RowId": 7, "employees_state": {"name": "active"}}], "fieldErrors": []}


# Edit: http://localhost:8080/ordermanagement-api/employees  POST
# action	edit
# data[7][employees][abbr]	FF
# data[7][employees][firstname]	Fred
# data[7][employees][lastname]	Fisch
# data[7][employees][state]	inactive
#
# Reply
# {"status": "success", "data": [{"employees": {"idemployee": 7, "abbr": "FF", "firstname": "Fred", "lastname": "Fisch", "state": "inactive"},
# "DT_RowId": 7, "employees_state": {"name": "inactive"}}], "fieldErrors": []}


# Delete  http://localhost:8080/ordermanagement-api/employees  POST
# action	remove
# data[7][employees][idemployee]	7
# data[7][employees][abbr]	FF
# data[7][employees][firstname]	Fred
# data[7][employees][lastname]	Fisch
# data[7][employees][state]	inactive
# data[7][DT_RowId]	7
# data[7][employees_state][name]	inactive
#
# Reply
# {"status": "success", "data": [{"employees": {"idemployee": 1, "abbr": "ClNo", "firstname": "Claudio", "lastname": "Nold", "state": "active"},
# "DT_RowId": 1, "employees_state": {"name": "active"}}, {"employees": {"idemployee": 2, "abbr": "FrV\u00f6", "firstname": "Freddi", "lastname": "V\u00f6geli", "state": "inactive"}, "DT_RowId": 2, "employees_state": {"name": "inactive"}}, {"employees": {"idemployee": 4, "abbr": "JoTe", "firstname": "John", "lastname": "Test", "state": "active"}, "DT_RowId": 4, "employees_state": {"name": "active"}}, {"employees": {"idemployee": 6, "abbr": "SW", "firstname": "Sacha", "lastname": "Wittmann", "state": "active"}, "DT_RowId": 6, "employees_state": {"name": "active"}}], "fieldErrors": []}
