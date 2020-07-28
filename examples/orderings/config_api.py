import sqlalchemy
from sqlalchemy import Table

from flask_restful import Resource
from flask import current_app, request

import logging
from flask.logging import default_handler

from flask_squirrel.util.session_auth import token_auth

log = logging.getLogger('config_api')
log.setLevel(logging.INFO)
log.addHandler(default_handler)


class ConfigApi(Resource):
    method_decorators = {'post': [token_auth.login_required], 'put': [token_auth.login_required]}

    def __init__(self):
        # self.customview_spec = current_app.config['customview_spec']
        # self.translation_spec = current_app.config['translation_spec']
        # self.db_spec = current_app.config['db_spec']
        self.db_connect = current_app.config['db_connect']

    def get(self):
        result_dict, return_code = self._get_ordering_counter()

        log.debug('ConfigApi: {0}'.format(result_dict))
        return result_dict, return_code

    def put(self):
        try:
            in_data = request.get_json(force=True)
        except Exception as e:
            msg = 'Request data is not JSON! mimetype:{0} type:{1} content:<{2}> exception:{3}'.\
                  format(request.mimetype, type(request.data), request.data, e)
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400
        log.debug('incoming request data:')
        log.debug(in_data)

        # do not expect a 'data' structure here
        # if 'data' not in in_data:
        #     msg = 'Config PUT request has no data field; nothing done!'
        #     return {'status': 'error', 'error': msg}, 400

        result_dict, return_code = self._execute_put_request(in_data)
        return result_dict, return_code

    def _get_ordering_counter(self):
        config: Table = current_app.config['db']['config']
        sel = config.select(whereclause=sqlalchemy.sql.text('config.idconfig=1'))
        try:
            result = self.db_connect.execute(sel)
        except sqlalchemy.exc.IntegrityError as e:
            msg = 'error getting config: {0}'.format(e)
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        row = result.fetchone()
        if row and (row['key'] == 'ordering_counter'):
            return {'data': {'ordering_counter': row['value']}}, 200
        else:
            msg = 'Error getting config row for ordering_counter, using default 1000'  # TODO: <--- default
            log.error(msg)
            ins = config.insert().values(idconfig=1, key='ordering_counter', value='1000')
            try:
                self.db_connect.execute(ins)
            except sqlalchemy.exc.IntegrityError as e:
                msg = 'error creating a new ordering_counter config: {0}'.format(e)
                log.error(msg)
                return {'status': 'error', 'error': msg}, 400

        return {'data': {'ordering_counter': 1000}}, 200  # TODO: <--- default

    def _execute_put_request(self, in_data):
        if 'ordering_counter' in in_data:
            new_counter_value = in_data['ordering_counter']
            result_dict, return_code = self._save_ordering_counter(new_counter_value)
            return result_dict, return_code

        msg = 'error in config: unknown or empty object: {0}'.format(in_data)
        log.error(msg)
        return {'status': 'error', 'error': msg}, 400

    def _save_ordering_counter(self, new_counter_value):
        config: Table = current_app.config['db']['config']
        sel = config.select(whereclause=sqlalchemy.sql.text('config.idconfig=1'))
        try:
            result = self.db_connect.execute(sel)
        except sqlalchemy.exc.IntegrityError as e:
            msg = 'error getting config: {0}'.format(e)
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        row = result.fetchone()
        if row and (row['key'] == 'ordering_counter'):
            upd = config.update().values(idconfig=1, key='ordering_counter', value=str(new_counter_value))
            try:
                self.db_connect.execute(upd)
            except sqlalchemy.exc.IntegrityError as e:
                msg = 'error updating ordering_counter config: {0}'.format(e)
                log.error(msg)
                return {'status': 'error', 'error': msg}, 400
        else:
            msg = 'Error getting config row for ordering_counter, using default 1000'  # TODO: <--- default
            log.error(msg)
            return {'status': 'error', 'error': msg}, 400

        log.info('saved new config value {0}: {1}'.format('ordering_counter', new_counter_value))
        return {'data': {'ordering_counter': new_counter_value}}, 200
