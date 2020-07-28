import hashlib
import os

from tests.api_employees import empl_api
from tests.api_orderings import ord_api
from tests.api_tools import ApiClient
from tests.api_upload import UploadFile
from tests.client_app_config import client_config

"""
Important Note:
'documents' has a special meaning compared to all other database resources: it's coupled together with files! So each
time you add or remove a document entry you add or remove a file also.

How it works:
1. Upload a file with the upload route 'upload'. This is already done in the other unit test.
2. Creating a new document means: add a table entry for it AND move the file from the upload pool to the archive path.
3. Deleting the document entry will also delete the file in the archive.  
"""


class DocumentsData(ApiClient):
    document1 = {
        'name': 'Order 1', 'filename': UploadFile.UPLOAD_FILE_LIST[0][2], 'type': 'order',
        'filedate': '2019-09-04', 'idemployee_added': empl_api.id_employee1,
        'idordering': ord_api.id_order1, 'comment': 'delayed 123', 'state': 'assigned'
    }

    document2_err1 = {
        'name': 'Order 2', 'filename': 'does_not_exists.pdf', 'type': 'order',
        'filedate': '2019-09-04', 'idemployee_added': empl_api.id_employee1,
        'idordering': ord_api.id_order1, 'comment': 'delayed 123', 'state': 'assigned'
    }

    document2 = {  # should fail because the file is already existing
        'name': 'Order 1', 'filename': UploadFile.UPLOAD_FILE_LIST[1][2], 'type': 'order',
        'filedate': '2019-09-04', 'idemployee_added': empl_api.id_employee1,
        'idordering': ord_api.id_order1, 'comment': 'delayed 123', 'state': 'assigned'
    }

    document3 = {
        'name': 'Order Confirmation 1', 'filename': UploadFile.UPLOAD_FILE_LIST[2][2], 'type': 'orderconfirmation',
        'filedate': '2020-02-02', 'idemployee_added': empl_api.id_employee1,
        'idordering': ord_api.id_order1, 'comment': 'delayed 345', 'state': 'assigned'
    }

    document4 = {
        'name': 'Delivery 1', 'filename': UploadFile.UPLOAD_FILE_LIST[3][2], 'type': 'delivery',
        'filedate': '2020-02-10', 'idemployee_added': empl_api.id_employee2,
        'idordering': ord_api.id_order2, 'comment': 'delayed 567', 'state': 'assigned'
    }

    document5 = {
        'name': 'Invoice 1', 'filename': UploadFile.UPLOAD_FILE_LIST[4][2], 'type': 'invoice',
        'filedate': '2020-02-10', 'idemployee_added': empl_api.id_employee2,
        'idordering': ord_api.id_order2, 'comment': 'delayed 567', 'state': 'assigned'
    }

    document4_edit = {
        'name': 'Order 2', 'filename': UploadFile.UPLOAD_FILE_LIST[3][2], 'type': 'delivery',
        'filedate': '2020-02-10', 'idemployee_added': empl_api.id_employee2,
        'idordering': ord_api.id_order3, 'comment': 'delayed 567 - changed to different order', 'state': 'assigned'
    }

    document4_edit2 = {
        'name': 'Order 2 edit2', 'filename': UploadFile.UPLOAD_FILE_LIST[3][2], 'type': 'delivery',
        'filedate': '2020-02-10', 'idemployee_added': empl_api.id_employee3,
        'idordering': ord_api.id_order3, 'comment': 'delayed 567 - changed to different employee', 'state': 'assigned'
    }

    document4_edit_new_filename = 'Proj_XYZ_2015-01_X/delivery_2020-02-10.txt'

    TESTFILE_LIST = [
        # doc dict, success, uploaded file path,              uploaded file name only,           expected archived file path and name
        (document1, True,  UploadFile.UPLOAD_FILE_LIST[0][1], UploadFile.UPLOAD_FILE_LIST[0][2], 'Proj_ABC_2019-10_A/order_2019-09-04.txt'),
        (document2, False, UploadFile.UPLOAD_FILE_LIST[1][1], UploadFile.UPLOAD_FILE_LIST[1][2], 'Proj_ABC_2019-10_A/order_2019-09-04.txt'),
        (document3, True,  UploadFile.UPLOAD_FILE_LIST[2][1], UploadFile.UPLOAD_FILE_LIST[2][2], 'Proj_ABC_2019-10_A/orderconfirmation_2020-02-02.txt'),
        (document4, True,  UploadFile.UPLOAD_FILE_LIST[3][1], UploadFile.UPLOAD_FILE_LIST[3][2], 'Proj_DEF_2020-11_B/delivery_2020-02-10.txt'),
        (document5, True,  UploadFile.UPLOAD_FILE_LIST[4][1], UploadFile.UPLOAD_FILE_LIST[4][2], 'Proj_DEF_2020-11_B/invoice_2020-02-10.txt'),
    ]

    def __init__(self):
        ApiClient.__init__(self, 'documents')
        self.db_spec = client_config.db_spec
        self.customview_spec = client_config.customview_spec
        self.id_document = []

    def initial_data(self):
        self.query_size(0)
        self.login_admin()  # assertion if failed
        self._create_tests()
        self._delete_tests()
        self._edit_tests()

    def _create_tests(self):
        for test_entry in self.TESTFILE_LIST:
            # first check uploaded documents in pool
            removed = self._check_file_upload_removed(test_entry[3])
            assert not removed, 'Uploaded file {0} does not exist but should'.format(test_entry[3])

            file_hash = self._get_hash_sha1hex(test_entry[2])
            expected_code = 400
            if test_entry[1]:
                expected_code = 200
            reply = self.api_create_entry(0, test_entry[0], expected_code)
            if not test_entry[1]:
                # do not check anything if the post request *should* have been failed
                continue
            self.check_reply(reply, test_entry[0])
            self.id_document.append(self.get_primary_id(reply, self.db_spec))

            removed = self._check_file_upload_removed(test_entry[3])
            assert removed, 'Uploaded file \'{0}\' should be moved and not exist in upload pool'.format(test_entry[3])

            archive_succeed = self._check_archived_file(test_entry[4], file_hash)
            assert archive_succeed, 'The uploaded file \'{0}\' has not been archived to {1}'.format(test_entry[3], test_entry[4])

        self.query_size(4)

        # try to save a document entry of a file which has not been uploaded before; this should fail
        reply = self.api_create_entry(0, self.document2_err1, 400)
        assert 'error' in reply, 'Creating a document without file correctly failed but did not give an error message: {0}'.format(reply)
        assert self.document2_err1['filename'] in reply['error'], 'The error reply does not contain the filename {0}'.format(self.document2_err1['filename'])
        assert 'not found' in reply['error'], 'The error reply does not contain the correct text: {0}'.format(reply['error'])

        # now check if the document2 really has NOT been written
        self.query_size(4)
        file_count = sum(len(files) for _, _, files in os.walk(client_config.archive_dir))
        assert file_count == 4, 'There should be 4 archived files, but found {0}: {1}'.format(file_count,
                                [files for _, _, files in os.walk(client_config.archive_dir)])

        # TODO: check not-existing upload and/or archive dir
        # TODO: check error if not writable directories

    def _delete_tests(self):
        self.query_size(4)
        # delete the last document
        reply = self.api_remove_entry(self.id_document[-1])
        self.query_size(3)
        removed_succeed = self._check_archive_removed(self.TESTFILE_LIST[4][4])
        assert removed_succeed, 'The archived file \'{0}\' has not been removed'.format(self.TESTFILE_LIST[4][4])
        file_count = sum(len(files) for _, _, files in os.walk(client_config.archive_dir))
        assert file_count == 3, 'There should be 3 archived files, but found {0}: {1}'.format(file_count,
                                [files for _, _, files in os.walk(client_config.archive_dir)])

        # delete the last document again - should fail
        reply = self.api_remove_entry(self.id_document[-1], None, 400)
        self.query_size(3)
        file_count = sum(len(files) for _, _, files in os.walk(client_config.archive_dir))
        assert file_count == 3, 'There should be 3 archived files, but found {0}: {1}'.format(file_count,
                                [files for _, _, files in os.walk(client_config.archive_dir)])

        # delete something not existing - should fail
        reply = self.api_remove_entry(99999, None, 400)
        self.query_size(3)
        file_count = sum(len(files) for _, _, files in os.walk(client_config.archive_dir))
        assert file_count == 3, 'There should be 3 archived files, but found {0}: {1}'.format(file_count,
                                [files for _, _, files in os.walk(client_config.archive_dir)])

        del self.id_document[-1]

        # TODO: delete something which we don't have file permissions for it

    def _edit_tests(self):
        id_document4 = self.id_document[-1]
        old_file_path = os.path.join(client_config.archive_dir, self.TESTFILE_LIST[3][4])
        new_file_path = os.path.join(client_config.archive_dir, self.document4_edit_new_filename)
        assert os.path.isfile(old_file_path), 'Old file {0} does not exist before it will be moved'.format(old_file_path)
        assert not os.path.isfile(new_file_path), 'New file {0} is already existing before creation'.format(self.document4_edit_new_filename)
        file_hash = self._get_hash_sha1hex(old_file_path)
        reply = self.api_edit_entry(id_document4, self.document4_edit)
        self.check_reply(reply, self.document4_edit)

        # now check if the location of the file has been changed to a new path
        assert not os.path.isfile(old_file_path), 'Old file {0} has NOT been removed after edit operation'.format(old_file_path)
        assert os.path.isfile(new_file_path), 'New file {0} not created!'.format(new_file_path)
        assert file_hash == self._get_hash_sha1hex(new_file_path), 'New file {0} was created but has not the same content like the old file'.format(new_file_path)
        self.query_size(3)

        # now edit the the document on columns which do not affect the name
        reply = self.api_edit_entry(id_document4, self.document4_edit2)
        self.check_reply(reply, self.document4_edit2)
        assert os.path.isfile(new_file_path), 'File {0} is not existing any more but should!'.format(new_file_path)
        assert file_hash == self._get_hash_sha1hex(new_file_path), 'File {0} has been changed but should not'.format(new_file_path)
        self.query_size(3)
        file_count = sum(len(files) for _, _, files in os.walk(client_config.archive_dir))
        assert file_count == 3, 'There should be 3 archived files, but found {0}: {1}'.format(file_count,
                                [files for _, _, files in os.walk(client_config.archive_dir)])

    @staticmethod
    def _check_file_upload_removed(filename):
        upload_filename = os.path.join(client_config.upload_dir, filename)
        return not os.path.isfile(upload_filename)  # true means: removed/not existing

    def _check_archived_file(self, path_filename, file_hash):
        archive_filename = os.path.join(client_config.archive_dir, path_filename)
        if not os.path.isfile(archive_filename):
            return False
        return file_hash == self._get_hash_sha1hex(archive_filename)

    @staticmethod
    def _check_archive_removed(path_filename):
        archive_filename = os.path.join(client_config.archive_dir, path_filename)
        return not os.path.isfile(archive_filename)

    @staticmethod
    def _get_hash_sha1hex(full_filename):
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
        sha1 = hashlib.sha1()

        with open(full_filename, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()

    def _check_file_archive_moved(self, document):
        if 'filename' not in self.customview_spec:
            return False
        filename_spec = self.customview_spec['filename']
        rel_path = filename_spec['fieldname']  # TODO: this is a bit too hardcoded
        archive_filepath = os.path.join(client_config.archive_dir, rel_path)
        archive_filename = os.path.join(archive_filepath, document['filename'])
        return os.path.isfile(archive_filename)


doc_api = DocumentsData()
