from flask_squirrel.table.dbutil import get_label_for_lang

from flask_restful import Resource
from flask import request, current_app
import re

import logging
from flask.logging import default_handler
log = logging.getLogger('viewspec')
log.setLevel(logging.INFO)
log.addHandler(default_handler)


class ResourceViewSpec(Resource):
    def __init__(self):
        self.customview_spec = current_app.config['customview_spec']
        self.translation_spec = current_app.config['translation_spec']
        self.db_spec = current_app.config['db_spec']

    def get(self):
        if current_app.config['db_fail']:
            # no DB connection, wrong config -> deny access
            return {'status': 'error', 'error': current_app.config['db_fail_err']}, 400

        # parse ISO631 language code
        lang = 'en'  # default
        if 'language' in request.args:
            lang_tmp = request.args['language']
            if re.match('^[a-z]{2}$', lang_tmp):
                lang = lang_tmp
        log.info('Resource view specification API request: passing language {0}'.format(lang))
        global current_lang
        current_lang = lang

        view_spec = self._generate_resource_view_spec(lang)
        everyone, admin = self._generate_auth_list()

        # log.info('* API {0} request args: {1}'.format(request.method, request.args))
        log.debug('ResourceViewSpec: {0}'.format(view_spec))
        return {'data': view_spec, 'auth': {'everyone_write': everyone, 'admin_write': admin}}

    def _generate_auth_list(self):
        everyone_writable_tables = []
        admin_writable_admin = []

        for table_name in self.db_spec:
            if table_name in self.customview_spec:
                if '_attributes' in self.customview_spec[table_name]:
                    if 'write_everyone' in self.customview_spec[table_name]['_attributes']:
                        everyone_writable_tables.append(table_name)

                    if 'write_table_admin' in self.customview_spec[table_name]['_attributes']:
                        admin_writable_admin.append(table_name)

        return everyone_writable_tables, admin_writable_admin

    def _generate_resource_view_spec(self, lang):
        # generate the resource view specification out of the 3 passed json files
        view_spec = {}
        everyone_writable_tables = []
        admin_writable_admin = []

        for table_name in self.db_spec:
            if table_name in self.customview_spec:
                if '_attributes' in self.customview_spec[table_name]:
                    if 'write_everyone' in self.customview_spec[table_name]['_attributes']:
                        everyone_writable_tables.append('table_name')

                    if 'write_table_admin' in self.customview_spec[table_name]['_attributes']:
                        admin_writable_admin.append('table_name')

                    if 'hidden' in self.customview_spec[table_name]['_attributes']:
                        # this is a table which is not show on the user interface as it used by the backend itself
                        continue

            self._generate_table(lang, table_name, view_spec)

        return view_spec

    def _generate_table(self, lang, table_name, view_spec):
        # table_spec = self.db_spec[table_name]
        view_spec[table_name] = {}
        table_label = self.translation_spec[table_name][table_name]
        view_spec[table_name]['label'] = get_label_for_lang(lang, table_label)

        # unused some editor fields in view spec: view_spec[table_name]['editor-fields'] = []
        # unused some table fields in view spec: view_spec[table_name]['table-fields'] = []
