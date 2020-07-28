import abc
import os
from shutil import copyfile

import sqlalchemy
from sqlalchemy import Table

from flask_squirrel.table.dbutil import get_primarykey_colname
from flask_squirrel.util.fileutils import get_valid_filename, get_file_list

import logging
from flask.logging import default_handler
log = logging.getLogger('linked_resource')
log.setLevel(logging.DEBUG)  # INFO
log.addHandler(default_handler)


class LinkedResource(metaclass=abc.ABCMeta):
    def __init__(self, args):
        self.table_name = args['table_name']
        self.col_name = args['col_name']
        self.customview_spec = args['customview_spec']
        self.translation_spec = args['translation_spec']
        self.db_spec = args['db_spec']
        self.db_connect = args['db_connect']
        self.db_reflection = args['db_reflection']
        self.db_placeholder_parser = args['db_placeholder_parser']

    @abc.abstractmethod
    def create_check(self, new_res):
        return True

    @abc.abstractmethod
    def create(self, new_res):
        return True

    @abc.abstractmethod
    def read_check(self, existing_res):
        pass

    @abc.abstractmethod
    def read(self, existing_res):
        pass

    @abc.abstractmethod
    def edit_check(self, row_id, new_res):
        pass

    @abc.abstractmethod
    def edit(self, new_res, previous_row):
        pass

    @abc.abstractmethod
    def delete_check(self, primary_id_to_remove):
        pass

    @abc.abstractmethod
    def delete(self, primary_id_to_remove, previous_row):
        pass

    @abc.abstractmethod
    def modify_linked_entry(self, db_row):
        pass


class FileResource(LinkedResource):
    LINK_COLUMN = 'filename'

    def __init__(self, args):
        """
        FileResource: this is a file which is linked to a row/entry from a specific table.
        Examples: - a user picture which is connected to the users table
                  - a PDF file which is connected to a document row/entry (e.g. ordering confirmation in a project )
        """
        super().__init__(args)
        self.upload_dir = args['upload_dir']
        self.file_url_path = args['file_url_path']
        self.archive_url_path = args['archive_url_path']
        self.archive_dir = args['archive_dir']

        # As this is a linked FILE resource it must be linked to a column in the table. This column will be
        # modified with a link to this file. So there must be a specification of what exactly is linked.
        # Example: "documents": { "filename": { "filelink": ....
        column_spec = self.customview_spec[self.table_name][self.LINK_COLUMN]
        self.linked_url_base = column_spec['filelink']  # may contain placeholders
        self.linked_path = column_spec['file_path']  # may contain placeholders
        self.rename_rule = column_spec['rename_rule']  # may contain placeholders and/or SQL table path

    def create_check(self, new_res):
        """
        See what the create() method does. create_check() has be called previously if it will succeed or not and gives
        some information why it will fail (eg. file not found).
        :param new_res:
        :return:
        """
        log.info('check for create new file: {0}'.format(new_res))
        succeed, msg, filename_to_save, new_file_path = self._prepare_check_create(new_res)
        if not succeed:
            return False, msg, None

        if not self._is_writable_dir(self.upload_dir):
            return False, 'upload dir {0} must be writable to move the file'.format(self.upload_dir), None

        # The base archive directory has to be writable but the new path has not to exist already.
        # This means if the base archive is writable it is expected to be working.
        # TODO for delete: archive_path = os.path.split(new_file_path)[0]
        if not self._is_writable_dir(self.archive_dir):
            return False, 'archive path {0} must be writable'.format(self.archive_dir), None

        if os.path.isfile(os.path.join(self.archive_dir, new_file_path)):
            return False, 'new file {0} is already existing!'.format(new_file_path), None

        return True, None, None

    def create(self, new_res):
        """ "Create" means: a document which is previously stored in the upload pool will be moved to an archive
        location. The archive path and the document renaming will be done according to the customview_spec.json.
        :param new_res:
        :return:
        """
        log.info('create new file: {0}'.format(new_res))
        succeed, msg, filename_to_save, new_file_path = self._prepare_check_create(new_res)
        if not succeed:
            return False, msg

        # now move the file from the upload path to the archive dir
        msg, new_rel_path = self._store_uploaded_file(filename_to_save, new_file_path)
        if msg:
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400
        return True, None

    def _prepare_check_create(self, new_res):
        # Only check if it will work
        if self.LINK_COLUMN not in new_res:
            msg = 'Error column {0} not found'.format(self.LINK_COLUMN)
            log.error(msg)
            return False, msg, None, None

        filename_to_save = new_res[self.LINK_COLUMN]

        # first check if the UI selected file is available in the upload directory
        files = get_file_list(self.upload_dir, self.file_url_path)
        uploaded_file_list = [f for f in files if f['name'] == filename_to_save]

        # selected_filename = current_app.config[self.API_TABLE_NAME]['selected_filename']
        # uploaded_file_list = [f for f in files if f['name'] == selected_filename]
        if len(uploaded_file_list) != 1:
            msg = 'Uploaded file \'{0}\' not found in directory \'{1}\' (len:{2})'\
                  .format(filename_to_save, self.archive_dir, len(uploaded_file_list))
            log.error(msg)
            return False, msg, None, None

        # now get the name out of the rename rule
        gen_suc, err_msg, new_file_path = self._generate_archive_file_path(new_res)
        if not gen_suc:
            return False, err_msg, None, None

        return True, None, filename_to_save, new_file_path

    def _generate_archive_file_path(self, base_res_dict):
        # now get the name out of the rename rule
        result, err_msg = self.db_placeholder_parser.parse(self.table_name, self.LINK_COLUMN, base_res_dict, self.rename_rule)
        if not result:
            return False, err_msg, None

        # the placeholder may specify a full path and therefore every part needs to be conform to the OS path rules
        new_file_path = ''
        for part in result.split(os.path.sep):
            # split, convert and join again every part of the path
            if part != '..':
                # do not accept relative backward path as it could be a security thread
                new_file_path = os.path.join(new_file_path, get_valid_filename(part))

        return True, None, new_file_path

    @staticmethod
    def _is_writable_dir(dir):
        if os.access(dir, os.W_OK) and os.path.isdir(dir):
            return True
        return False

    @staticmethod
    def _is_writable_file(filename):
        if os.access(filename, os.W_OK) and os.path.isfile(filename):
            return True
        return False

    def read_check(self, existing_res):
        pass

    def read(self, existing_res):
        """
        "Read" means: give access to the file by providing the URL path from the archive
        :param existing_res:
        :return:
        """
        pass

    def edit_check(self, row_id, new_res):
        previous_row, err_msg = self._load_row_by_id(row_id)
        if not previous_row:
            return False, err_msg, None

        if self.LINK_COLUMN not in previous_row:
            msg = 'Error column {0} not found'.format(self.LINK_COLUMN)
            log.error(msg)
            return False, msg, previous_row

        # get the OLD name out of the rename rule
        gen_suc, err_msg, old_archive_file_path = self._generate_archive_file_path(previous_row)
        if not gen_suc:
            return False, err_msg, previous_row

        if not os.path.isfile(os.path.join(self.archive_dir, old_archive_file_path)):
            return False, 'cannot move archived file {0} as it is NOT existing!'.format(old_archive_file_path), previous_row
        if not self._is_writable_file(os.path.join(self.archive_dir, old_archive_file_path)):
            return False, 'cannot delete archived file {0} as there is not sufficient access permission!'.format(old_archive_file_path), previous_row

        # get the NEW name out of the rename rule
        gen_suc, err_msg, new_archive_file_path = self._generate_archive_file_path(new_res)
        if not gen_suc:
            return False, err_msg, previous_row

        if old_archive_file_path == new_archive_file_path:
            # accept changes which do not affect the file names
            return True, None, previous_row

        if os.path.isfile(os.path.join(self.archive_dir, new_archive_file_path)):
            return False, 'new file {0} is already existing; old {1} cannot be moved!'.format(new_archive_file_path, old_archive_file_path), previous_row

        if not self._is_writable_dir(self.archive_dir):  # only check the base dir because the intermediate path could be new/not existing
            return False, 'the archive path {0} is not writable!'.format(self.archive_dir), previous_row

        return True, None, previous_row

    def edit(self, new_res, previous_row):
        """
        "Edit" means: replace the file or rename it. The file could even change the storage location.
        :param new_res:
        :param previous_row:
        :return:
        """
        gen_suc, err_msg, old_archive_file_path = self._generate_archive_file_path(previous_row)
        if not gen_suc:
            return False, err_msg
        gen_suc, err_msg, new_archive_file_path = self._generate_archive_file_path(new_res)
        if not gen_suc:
            return False, err_msg

        if old_archive_file_path == new_archive_file_path:
            # accept changes which do not affect the file names
            return True, None

        move_succeed, err_msg = self._move_archive_file(old_archive_file_path, new_archive_file_path)
        if not move_succeed:
            return False, err_msg

        return True, None

    def delete_check(self, primary_id_to_remove):
        previous_row, err_msg = self._load_row_by_id(primary_id_to_remove)
        if not previous_row:
            return False, err_msg, None

        if self.LINK_COLUMN not in previous_row:
            msg = 'Error column {0} not found'.format(self.LINK_COLUMN)
            log.error(msg)
            return False, msg, previous_row

        # now get the name out of the rename rule
        gen_suc, err_msg, archive_file_path = self._generate_archive_file_path(previous_row)
        if not gen_suc:
            return False, err_msg, previous_row

        # This is not really clear: should we always use the generated full file path or should we use some stored name
        # in row[self.LINK_COLUMN]?

        if not os.path.isfile(os.path.join(self.archive_dir, archive_file_path)):
            return False, 'cannot delete archived file {0} as it is NOT existing!'.format(archive_file_path), previous_row

        if not self._is_writable_file(os.path.join(self.archive_dir, archive_file_path)):
            return False, 'cannot delete archived file {0} as there is not sufficient access permission!'.format(archive_file_path), previous_row

        return True, None, previous_row

    def delete(self, primary_id_to_remove, previous_row):
        """
        "Delete" means: delete file from the archive path. The path will be clear if no file or directory remains in it.
        """

        gen_suc, err_msg, archive_file_path = self._generate_archive_file_path(previous_row)
        if not gen_suc:
            return False, err_msg

        archive_file = os.path.join(self.archive_dir, archive_file_path)
        try:
            os.remove(archive_file)
        except OSError as e:
            err_msg = 'Failed to delete file \'{0}\': {1}'.format(archive_file, e.strerror)
            return False, err_msg

        return True, err_msg

    def modify_linked_entry(self, db_row):
        log.info('DB row linked to file: {0}'.format(db_row))
        gen_suc, err_msg, archive_file_path = self._generate_archive_file_path(db_row[self.table_name])
        if not gen_suc:
            return

        db_row[self.table_name][self.col_name + '_link'] = self.archive_url_path + '/' + archive_file_path

    def _store_uploaded_file(self, file_to_store, new_file_name):
        errmsg = None
        src = os.path.join(self.upload_dir, file_to_store)
        dst_path = os.path.join(self.archive_dir, os.path.split(new_file_name)[0])  # this is the path only without file name

        try:
            if dst_path and (not os.path.exists(dst_path)):
                os.mkdir(dst_path)
        except OSError as e:
            errmsg = 'Failed to create directory \'{0}\' for file \'{1}\': {2}'\
                     .format(dst_path, file_to_store, e.strerror)
            return errmsg, None

        dst = os.path.join(dst_path, os.path.split(new_file_name)[1])

        try:
            copyfile(src, dst)
            os.remove(src)
        except OSError as e:
            errmsg = 'Failed to move file \'{0}\' to {1}: {2}'.format(src, dst, e.strerror)
        return errmsg, dst_path

    def _delete_uploaded_file(self, file_to_delete):
        errmsg = None
        fullfile_path = os.path.join(self.managed_dir, file_to_delete)   #  <------------- <----------
        try:
            os.remove(fullfile_path)
        except OSError as e:
            errmsg = 'Failed to delete file \'{0}\': {1}'.format(fullfile_path, e.strerror)
        return errmsg

    def _load_row_by_id(self, row_id):
        table: Table = self.db_reflection[self.table_name]
        primarykey_name = get_primarykey_colname(self.table_name, self.db_spec)
        sel = table.select(whereclause=sqlalchemy.sql.text('{0}.{1}={2}'.format(self.table_name, primarykey_name, row_id)))
        try:
            result = self.db_connect.execute(sel)
        except sqlalchemy.exc.IntegrityError as e:
            return None, 'SQL error reading table \'{0}\' where \'{1}={2}\': {0}'.format(self.table_name, primarykey_name,
                                                                                         row_id, e)

        row = result.fetchone()
        if not row:
            return None, 'SQL error reading table \'{0}\' where \'{1}={2}\' (empty results)'. \
                format(self.table_name, primarykey_name, row_id)
        return row, None

    def _move_archive_file(self, old_archive_file_path, new_archive_file_path):
        src_file = os.path.join(self.archive_dir, old_archive_file_path)
        dst_path = os.path.join(self.archive_dir, os.path.split(new_archive_file_path)[0])  # this is the path only without file name

        try:
            if dst_path and (not os.path.exists(dst_path)):
                os.mkdir(dst_path)
        except OSError as e:
            errmsg = 'Failed to create directory \'{0}\' for file \'{1}\': {2}'\
                     .format(dst_path, new_archive_file_path, e.strerror)
            return errmsg, None

        dst = os.path.join(dst_path, os.path.split(new_archive_file_path)[1])

        try:
            copyfile(src_file, dst)
            os.remove(src_file)
        except OSError as e:
            return False, 'Failed to move file \'{0}\' to {1}: {2}'.format(src_file, dst, e.strerror)
        return True, None


def link_resource_factory(table_name, col_name, col_viewspec, app_conf):
    resource = None

    factory_args = {
        'table_name': table_name,
        'col_name': col_name,
        'col_viewspec': col_viewspec,
        'customview_spec': app_conf['customview_spec'],
        'translation_spec': app_conf['translation_spec'],
        'db_spec': app_conf['db_spec'],
        'db_connect': app_conf['db_connect'],
        'db_reflection': app_conf['db'],  # this is the SQL alchemy table reflection
        'db_placeholder_parser': app_conf['db_placeholder_parser']
    }

    if 'filelink' in col_viewspec:
        factory_args['upload_dir'] = app_conf['upload_dir']
        factory_args['file_url_path'] = app_conf['file_url_path']
        factory_args['archive_url_path'] = app_conf['archive_url_path']
        factory_args['archive_dir'] = app_conf['archive_dir']
        resource = FileResource(factory_args)

    return resource
