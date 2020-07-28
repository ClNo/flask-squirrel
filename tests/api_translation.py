from typing import List

from tests.api_tools import ApiClient
from tests.client_app_config import client_config


class TranslationTest(ApiClient):
    TRANSLATION_TABLES: List[str] = ['users', 'projects', 'orderings', 'suppliers', 'documents']
    LANGUAGES: List[str] = ['en', 'de']

    def __init__(self):
        ApiClient.__init__(self, '-undef-')  # API resource name will change on tests
        self.db_spec = client_config.db_spec

    def translation_test(self):
        for table in self.TRANSLATION_TABLES:
            editor_trans = []
            for lang_code in self.LANGUAGES:
                self.set_api_path(table)
                req_args = {'lang': lang_code}
                result = self.api_request_get(expected_result=200, args=req_args)
                assert result is not None, 'query to table {0} returned empty result'.format(table)
                assert 'translation' in result, 'query to table {0} should contain a \'translation\' field'.format(table)

                for lang_elem in result['translation']:
                    assert len(result['translation'][lang_elem]) > 0,\
                           'Editor translation element {0}._editor.{1} is empty'.format(table, lang_elem)

                # loose the language here (lang_code)
                editor_trans.append(result['translation'])

            # now check if there is a difference between the languages (allow some duplicates)
            err_count = 0
            for idx in range(0, len(editor_trans)-1):
                for lang_elem in editor_trans[idx]:
                    text1 = editor_trans[idx][lang_elem]
                    text2 = editor_trans[idx+1][lang_elem]
                    if text1 == text2:
                        err_count += 1
                    if err_count > 1:
                        # allow some text duplicates - for instance 'name' is the same
                        assert text1 != text2, 'Editor translation element {0}._editor.{1}: element value "{2}" is ' \
                                               'the same on different languages'.format(table, lang_elem,
                                                                                        editor_trans[idx][lang_elem])


translation_api = TranslationTest()
