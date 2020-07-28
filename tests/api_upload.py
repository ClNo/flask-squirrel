from tests.api_tools import ApiClient
from tests.client_app_config import client_config
from flask import current_app

import os


class UploadFile(ApiClient):
    FILE_NAME_1 = 'tests/data/upload_file_order.txt'
    FILE_NAME_2 = 'tests/data/upload_file_confirmation.txt'
    FILE_NAME_3 = 'tests/data/upload_file_delivery.txt'
    FILE_NAME_4 = 'tests/data/upload_file_invoice.txt'
    FILE_NAME_5 = 'tests/data/upload_file_deleteme.txt'

    UPLOAD_FILE_LIST = [
        ('order', FILE_NAME_1, os.path.basename(FILE_NAME_1)),
        ('order', FILE_NAME_1, 'upload_file_order_2.txt'),
        ('orderconfirmation', FILE_NAME_2, os.path.basename(FILE_NAME_2)),
        ('delivery', FILE_NAME_3, os.path.basename(FILE_NAME_3)),
        ('invoice', FILE_NAME_4, os.path.basename(FILE_NAME_4)),
        ('invoice', FILE_NAME_5, os.path.basename(FILE_NAME_5)),
    ]

    def __init__(self):
        ApiClient.__init__(self, 'upload')
        self.db_spec = client_config.db_spec

    def upload_test(self):
        # self.query_size(0)
        # self._login_admin()  # assertion if failed
        # self._create_tests()
        # self.query_size(3)

        for fspec in self.UPLOAD_FILE_LIST:
            src_filename = fspec[1]
            filename = fspec[2]

            data = {
                'file': (open(src_filename, 'rb'), filename),
            }
            rv = self.client.post(self.res_path, data=data)
            assert rv.status_code == 200, 'upload failed: {0}'.format(rv.json)

            self._check_file_uploaded(src_filename, filename)

        # now do a delete request
        del_filename = self.UPLOAD_FILE_LIST[5][2]
        data = {'file': del_filename}
        rv = self.client.delete(self.res_path, data=data)
        # makes a 'HTTP_CONTENT_TYPE': 'application/x-www-form-urlencoded' request
        assert rv.status_code == 200, 'deleting uploaded file {0} failed: {1}'.format(del_filename, rv.json)

        # check if it has been removed
        upload_dir = current_app.config['upload_dir']
        upload_filename = os.path.join(upload_dir, del_filename)
        assert os.path.isfile(upload_filename) is False, 'uploaded file {0} should be removed in {1} now, but still exists'.format(del_filename, upload_dir)

    @staticmethod
    def _check_file_uploaded(src_filename, filename):
        upload_dir = current_app.config['upload_dir']
        upload_filename = os.path.join(upload_dir, filename)

        upload_size = os.stat(upload_filename).st_size
        src_size = os.stat(src_filename).st_size

        assert upload_size == src_size, 'Uploaded file {0} does not have the same size as the original'.format(src_filename)


upload_file = UploadFile()
