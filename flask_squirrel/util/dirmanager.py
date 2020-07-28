import datetime
from copy import deepcopy

import sqlalchemy
from sqlalchemy import Table

from flask_squirrel.table.dbtable import DbTable
from flask_squirrel.util.view_spec_generator import ViewSpecGenerator
from .fileutils import get_file_list

from flask import request, current_app
import os
from shutil import copyfile

import logging
log = logging.getLogger('dirmanager')
log.level = logging.DEBUG


class DirManager(DbTable):
    def __init__(self, **kwargs):
        DbTable.__init__(self, **kwargs)
        self.managed_dir = kwargs['managed_dir']
        self.archive_dir = current_app.config['archive_dir']  # this is the path where the file is stored on the disk
        self.file_url_path = current_app.config['file_url_path']  # this is the URL where file can be accessed on the server
        self.last_files = None
        if 'editor_assigner' in kwargs:
            self.editor_assigner = kwargs['editor_assigner']
        else:
            self.editor_assigner = None
        self.edited_index = None
        self.file_to_store = None

        self.view_spec_generator: ViewSpecGenerator = current_app.config['view_spec_generator']
        self.view_spec = None

    def get(self):
        args = self._parse_request_args()
        if 'lang' in args:
            self.current_lang = args['lang']


        # extract the currently set filter in the frontend
        current_editor_filter = {}
        if 'editor_filter' in request.args:
            editor_filter_inlist = request.args['editor_filter'].split('|')
            # example input string: 'documents.idordering:projects-running'
            for filter_def in editor_filter_inlist:
                field, current_filter_value = filter_def.split(':')
                # example: field = 'documents.idordering', current_filter_value = 'projects-running'
                filter_table,  filter_column = field.split('.')
                if filter_table not in current_editor_filter:
                    current_editor_filter[filter_table] = {}

                if (self.endpoint in self.customview_spec) and ('_editor_filters' in self.customview_spec[self.endpoint]):
                    avail_filters = self.customview_spec[self.endpoint]['_editor_filters']
                    if (field in avail_filters) and (current_filter_value in avail_filters[field]):
                        # finally found the editor filter -> save it!
                        filter_dict = avail_filters[field]  # all filters used here (not: [current_filter_value])
                        current_editor_filter[filter_table]['current_filter'] = current_filter_value

                        current_editor_filter[filter_table][filter_column] = filter_dict
                        # example: current_editor_filter = {'documents': {'idordering':  { "base_table": "orderings", ...}}

        empty_row_dict = DbTable._create_empty_row_dict(self, self.table_name)

        files = get_file_list(self.managed_dir, self.file_url_path)
        self.last_files = files.copy()
        table_data = []
        options_dict = None

        if args['get_data']:
            row_cnt = 1
            for file_row in files:
                table_row = {'documents': deepcopy(empty_row_dict),
                             'DT_RowId': row_cnt,
                             'name': os.path.splitext(file_row['name'])[0],
                             'size_hr': file_row['size_hr'],
                             'mtime': file_row['mtime'][:10],
                             'link': file_row['link'],
                             'filename': file_row['name'], 'state': 'assigned', 'filedate': file_row['mtime'][:10]}
                table_data.append(table_row)
                row_cnt += 1

            options_dict = DbTable._generate_options(self, current_editor_filter=current_editor_filter)

        if not self.view_spec:
            # TODO: generate the spec again if self.current_lang has been changed!
            self.view_spec = self.view_spec_generator.generate_default_spec('documents', self.current_lang)

        filters = None
        editor_filters = None
        if args['get_spec']:
            filters = DbTable._generate_filters(self, self.endpoint)
            editor_filters = DbTable._generate_editor_filters(self, self.endpoint)

        result = {'data': table_data,
                  'table-fields': [{'data': 'name', 'title': 'Name', 'editField': 'documents.name'}, {'data': 'size_hr', 'title': 'Size'},
                                   {'data': 'mtime', 'title': 'File Date', 'type': 'date'},
                                   {'data': 'link', 'title': 'Link'}],
                  'editor-fields': self.view_spec['editor-fields'],
                  'options': options_dict,
                  # note: self.table_name is set to 'documents' but here we use the specific filters of the filelist
                  #       table and editor. Therefore we take the 'endpoint' attribute which still points to the
                  #       'upload-filelist' route.
                  'filters': filters,
                  'editor-filters': editor_filters}

        log.debug('DirManager: {0}'.format(result))
        return result

    def post(self):
        return DbTable.post(self)

    def _handle_post_request(self, action, request_data, parameters):

        if action == 'create':
            msg = 'Action \'create\' in DirManager will create a new document: {0}'.format(request_data)
            log.info(msg)
            return DbTable._handle_post_request(self, action, request_data, parameters)

        # only one key == file supported
        self.edited_index = list(request_data.keys())[0]
        # self.file_to_store = request_data[self.edited_index]['documents']['filename']
        self.file_to_store = request_data[self.edited_index]['filename']
        if 'filename' in parameters:
            self.src_filename = parameters['filename']

        if action == 'remove':
            errmsg = self._delete_uploaded_file(self.file_to_store)
            if errmsg:
                return {'status': 'error', 'error': errmsg}, 404  # 404: NOT FOUND
            return {'status': 'success', 'data': None}, 200

        msg = 'Action type {0} unknown!'.format(action)
        log.error(msg)
        return {'status': 'error', 'error': msg}, 400

    def _store_uploaded_file(self, file_to_store, project_name, new_file_name):
        errmsg = None
        src = os.path.join(self.managed_dir, file_to_store)
        dst_path = os.path.join(self.archive_dir, project_name)
        dst_rel_path = os.path.join(project_name, new_file_name)

        try:
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)
        except OSError as e:
            errmsg = 'Failed to create directory \'{0}\' for file \'{1}\': {2}'\
                     .format(dst_path, file_to_store, e.strerror)
            return errmsg, None

        dst = os.path.join(dst_path, new_file_name)
        try:
            copyfile(src, dst)
            os.remove(src)
        except OSError as e:
            errmsg = 'Failed to move file \'{0}\' to {1}: {2}'.format(src, dst, e.strerror)
        return errmsg, dst_rel_path

    def _delete_uploaded_file(self, file_to_delete):
        errmsg = None
        fullfile_path = os.path.join(self.managed_dir, file_to_delete)
        try:
            os.remove(fullfile_path)
        except OSError as e:
            errmsg = 'Failed to delete file \'{0}\': {1}'.format(fullfile_path, e.strerror)
        return errmsg

    def _get_project_name_for_ordering(self, idordering):
        orderings: Table = current_app.config['db']['orderings']
        sel = orderings.select(whereclause=sqlalchemy.sql.text('orderings.idordering={0}'.format(idordering)))
        try:
            result = self.db_connect.execute(sel)
        except sqlalchemy.exc.IntegrityError as e:
            msg = 'error getting orderings: {0}'.format(e)
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        row = result.fetchone()
        if row:
            idproject = row['idproject']
        else:
            msg = 'Error getting idordering {0}'.format(idordering)
            log.error(msg)
            return None

        projects: Table = current_app.config['db']['projects']
        sel = projects.select(whereclause=sqlalchemy.sql.text('projects.idproject={0}'.format(idproject)))
        try:
            result = self.db_connect.execute(sel)
        except sqlalchemy.exc.IntegrityError as e:
            msg = 'error getting orderings: {0}'.format(e)
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        row = result.fetchone()
        return row['name']

    # do not handle error as this should never break closing the editor
    def _change_ordering_state(self, idordering, file_type):
        orderings: Table = current_app.config['db']['orderings']

        today_iso = datetime.date.today().isoformat()

        upd = None
        if file_type == 'order':
            new_state = 'ordered'
            upd = orderings.update().where(orderings.c.idordering == idordering)\
                           .values(order_state=new_state, date_ordered=today_iso)
        elif file_type == 'orderconfirmation':
            new_state = 'confirmed'
            # no field!!! date_field = 'date_delivered'
            upd = orderings.update().where(orderings.c.idordering == idordering)\
                           .values(order_state=new_state)
        elif file_type == 'delivery':
            new_state = 'delivered'
            upd = orderings.update().where(orderings.c.idordering == idordering)\
                           .values(order_state=new_state, date_delivered=today_iso)
        elif file_type == 'invoice':
            new_state = 'invoiced'
            upd = orderings.update().where(orderings.c.idordering == idordering)\
                           .values(order_state=new_state, date_invoiced_done=today_iso)

        if upd is None:
            return

        try:
            self.db_connect.execute(upd)
        except sqlalchemy.exc.IntegrityError as e:
            msg = 'error changing the ordering {0}: {1}'.format(idordering, e)
            log.error(msg)
