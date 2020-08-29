from flask import request, current_app, jsonify
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_restful import Resource
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import Table

import datetime
import json
import os
import secrets
import sqlalchemy

import logging
from flask.logging import default_handler
log = logging.getLogger('own_auth')
log.setLevel(logging.DEBUG)  # INFO
log.addHandler(default_handler)


AUTHENTICATION_TABLE = 'users'
AUTHENTICATION_ID = 'iduser'
AUTHENTICATION_LOGINNAME_1 = 'username'
AUTHENTICATION_LOGINNAME_2 = 'email'
AUTHENTICATION_CREDENTIAL = 'credential_hash'
AUTHENTICATION_LEVEL = 'authentication_level'

token_auth = HTTPTokenAuth('Bearer')
auth_login = HTTPBasicAuth()
auth = MultiAuth(auth_login, token_auth)


# This authentication function is only called for table accesses and NOT for the login route
@token_auth.verify_token
def verify_token(token):
    # verify_token - return value:
    #   False = token failed, authentication required; Flask will return a 401 http reply
    #   True  = token succeed, NO authentication required; everything's fine - continue the request

    # handle logout request here also (logout on every route is possible by sending the 'logout' argument)
    if LoginTokenApi.LOGOUT_PARAM in request.args:
        if current_app.user:
            current_app.user.end_session()
        current_app.user = None
        return True

    # first try to authenticate by token
    user, session_key = User.verify_auth_token(token)
    current_app.user = user
    if user:
        # the token is known and it is a valid user
        session_key_valid = user.is_session_key_valid(session_key)
        auth_required_after, is_login_route = is_auth_table_required()
        # auth_required_after means: this request needs admin access
        # TODO: access is currently only for admin - not admin and not user dependent
        if not auth_required_after:
            # the table does not require authentication
            return True  # NO authentication
        elif session_key_valid and user.is_admin():
            # the admin is allowed to do everything
            return True  # NO authentication for admin
        elif session_key_valid and auth_required_after:
            # the session key is valid but the table is not authenticated
            return False  # require authentication
        else:
            # the session key is invalid but the table require authentication
            return False  # require authentication

    # the token is unknown or empty -> check if the table requires an authentication at all
    # the table can be configured to be writable by anyone and/or readable by anyone
    auth_required_after, is_login_route = is_auth_table_required()
    # return False:  needs authentication
    #        True:   NO authentication needed
    return not auth_required_after


class User:
    def __init__(self, user_row):
        self.user = user_row
        self.password_hash = user_row.credential_hash

    def hash_password(self, password):
        self.user.credential_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        if not self.user:
            return False
        if 'credential_hash' not in self.user:
            return False

        try:
            return pwd_context.verify(password, self.user.credential_hash)
        except ValueError as e:
            log.error('Error verifying the new password against the existing hash: {0}'.format(e))
        return False

    def generate_auth_token(self, session_key, expiration_seconds):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration_seconds)
        return s.dumps({'id': self.user.iduser, 'session_key': session_key})

    def is_admin(self):
        if self.user['authentication_level'] > 0:
            return True
        return False

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None, None    # valid token, but expired
        except BadSignature:
            return None, None    # invalid token

        # here, the token is checked and verified

        user_row = User.read_user_row_from_db('{0}.{1}={2}'.format(AUTHENTICATION_TABLE, AUTHENTICATION_ID, data['id']))
        if not user_row:
            return None, None

        user = User(user_row)
        return user, data['session_key']

    @staticmethod
    def calc_hash_password(password):
        if not password:
            return None
        return pwd_context.encrypt(password)

    @staticmethod
    def read_user_row_from_db(filter_str):
        if current_app.config['db_fail']:
            # no DB connection, wrong config -> deny access
            return None

        db_connect = current_app.config['db_connect']
        employees: Table = current_app.config['db'][AUTHENTICATION_TABLE]
        sel = employees.select(whereclause=sqlalchemy.sql.text(filter_str))
        try:
            result = db_connect.execute(sel)
        except sqlalchemy.exc.SQLAlchemyError as e:
            msg = 'error getting user with WHERE {0}: {1}'.format(filter_str, e)
            log.error(msg)
            return None

        user_row = result.fetchone()
        if not user_row:
            return None

        return user_row

    @staticmethod
    def check_initial_user(app):
        if app.config['db_fail']:
            # no DB connection, wrong config -> deny access
            return False

        users: Table = app.config['db'][AUTHENTICATION_TABLE]
        sel = users.select()  # whereclause=sqlalchemy.sql.text('config.idconfig=1'))
        try:
            result = app.config['db_connect'].execute(sel)
        except sqlalchemy.exc.IntegrityError as e:
            msg = 'error getting employees: {0}'.format(e)
            log.error(msg)
            return False

        has_admin = False
        id_init_user = None
        for row in result:
            if row[AUTHENTICATION_LEVEL] and (row[AUTHENTICATION_LEVEL] > 0):
                has_admin = True

            if row[AUTHENTICATION_LOGINNAME_1] and (row[AUTHENTICATION_LOGINNAME_1] == app.config['default_admin_user'][AUTHENTICATION_LOGINNAME_1]):
                id_init_user = row[AUTHENTICATION_ID]

        if id_init_user is None:
            admin_config = app.config['default_admin_user']
            ins = users.insert() \
                .values({AUTHENTICATION_LOGINNAME_1: admin_config['username'],
                         'firstname': admin_config['firstname'],
                         'lastname': admin_config['lastname'],
                         AUTHENTICATION_CREDENTIAL: pwd_context.encrypt(admin_config['password']),
                         AUTHENTICATION_LEVEL: admin_config['authentication_level'],
                         'state': 'active'})

            try:
                result = app.config['db_connect'].execute(ins)
            except sqlalchemy.exc.IntegrityError as e:
                msg = 'error creating a default user: {0}'.format(e)
                log.error(msg)
                return False

        return True

    # --- session handling ---

    @staticmethod
    def generate_session_key():
        return secrets.token_hex(nbytes=32)  # 32 bytes * 8 bits = 256 bit safe encryption

    def get_session_filename(self):
        if not self.user:
            return ''
        if AUTHENTICATION_ID not in self.user:
            return ''
        if not self.user[AUTHENTICATION_ID]:
            return ''
        filename = 'session_{0}'.format(self.user[AUTHENTICATION_ID])
        return os.path.join(current_app.config['session_dir'], filename)

    def is_session_key_valid(self, key):
        if not key:
            return False
        filename = self.get_session_filename()
        if not filename:
            return False
        if not os.path.isfile(filename):
            return False

        # check the session validity within the file only
        try:
            with open(filename, 'r') as sf:
                session_dict = json.load(sf)
        except:
            return False
        if not session_dict['key']:
            return False
        return session_dict['key'] == key

    def new_session(self):
        filename = self.get_session_filename()
        if not filename:
            log.error('Session file name undefined: {0}'.format(self.user))
            return {}

        session_dict = {}
        try:
            with open(filename, 'r') as sf:
                session_dict = json.load(sf)
        except:
            log.debug('Session file not existing already: {0}'.format(filename))
        session_dict['name'] = self.user[AUTHENTICATION_LOGINNAME_1]
        session_dict['start_time'] = datetime.datetime.now().isoformat(timespec='minutes')
        session_dict['key'] = self.generate_session_key()
        try:
            with open(filename, 'w') as sf:
                json.dump(session_dict, sf, indent='\t')
        except Exception as e:
            log.error('Unable to save session file {0}: {1}'.format(filename, e))
        return session_dict

    def end_session(self):
        filename = self.get_session_filename()
        if not filename:
            log.debug('Session file name undefined: {0}'.format(self.user))
            return

        session_dict = {}
        try:
            with open(filename, 'r') as sf:
                session_dict = json.load(sf)
        except:
            log.debug('Session file not existing at all: {0}'.format(filename))
            return

        # clear the key so it will be invalid in future
        session_dict['key'] = None

        try:
            with open(filename, 'w') as sf:
                json.dump(session_dict, sf, indent='\t')
        except Exception as e:
            log.error('Unable to save session file {0}: {1}'.format(filename, e))


def is_auth_table_required():
    """
    Parse the request's URL and check if the table exists and requires an authentication.
    Also check it is a http GET request and if it's allowed to read by read by anyone.
    TODO: access is currently only for admin - not admin and not user dependent
    :return: authentication_required, is_login_route
    """
    url_table = request.url[request.url.rindex('/') + 1:]
    if len(url_table) < 2:
        log.error('authentication check: url contains no route!? [{0}]'.format(request.url))
        return True, False  # this will trigger a 401 response

    customview_spec = current_app.config['customview_spec']

    allow_write = False  # default: read only!
    allow_read = True  # TODO: default: read everyone; it's a bit dangerous...
    is_login_route = False

    if url_table in customview_spec:
        if '_attributes' in customview_spec[url_table]:
            if 'login_route' in customview_spec[url_table]['_attributes']:
                # for login: enforce login, otherwise we don't get in!
                allow_write = False
                is_login_route = True

            elif 'write_everyone' in customview_spec[url_table]['_attributes']:
                allow_write = True

            elif 'write_table_admin' in customview_spec[url_table]['_attributes']:
                allow_write = False  # this means it is not writable for everyone

    log.info('authentication for post request to {0}: allow_write={1}'.format(url_table, allow_write))

    if allow_write:
        # no authentication required; everything's fine
        return False, is_login_route

    if allow_read and request.method == 'GET':
        # no authentication required; everything's fine
        return False, is_login_route

    # authentication required
    return True, is_login_route


@auth_login.verify_password
def verify_password(username_or_token, password):
    if request.args.get(LoginTokenApi.LOGOUT_PARAM):
        if current_app.user:
            current_app.user.end_session()
        current_app.user = None
        return True

    # search in form data for token
    form_data = None
    if request.form:
        form_data = dict(request.form)
    elif request.data:
        form_data = json.loads(request.data.decode('utf-8'))
    elif request.json:
        form_data = request.json

    if not username_or_token:
        if form_data and ('auth_token' in form_data):
            # found token in form data -> check if it's valid
            username_or_token = form_data['auth_token']

    auth_required_before, is_login_route = is_auth_table_required()
    if not username_or_token:
        return not auth_required_before

    # first try to authenticate by token
    user, session_key = User.verify_auth_token(username_or_token)
    if user:
        current_app.user = user
        session_valid = user.is_session_key_valid(session_key)
        auth_required_after, is_login_route = is_auth_table_required()
        return not auth_required_after

    user_row = User.read_user_row_from_db('{0}.{1}="{2}"'.format(AUTHENTICATION_TABLE, AUTHENTICATION_LOGINNAME_1, username_or_token))
    if not user_row:
        return False

    user = User(user_row)
    if user and (not user.verify_password(password)):
        msg = 'error authentication of user: {0}'.format(username_or_token)
        log.error(msg)
        return False

    current_app.user = user
    auth_required_after, is_login_route = is_auth_table_required()
    if is_login_route:
        return True
    return not auth_required_after


class LoginTokenApi(Resource):
    LOGOUT_PARAM = 'logout'
    method_decorators = {'post': [auth.login_required], 'get': [auth.login_required]}

    def get(self):
        if self.LOGOUT_PARAM in request.args:
            msg = 'Logout succeed'
            log.info(msg)
            if current_app.user:
                current_app.user.end_session()
            current_app.user = None
            return {self.LOGOUT_PARAM: True}, 200

        if current_app.user:
            session_dict = current_app.user.new_session()
            if 'key' in session_dict:
                expiration_time = current_app.config['login_expiration_seconds']
                token = current_app.user.generate_auth_token(session_dict['key'], expiration_time)  # in seconds
                return jsonify({'token': token.decode('ascii'), 'duration': expiration_time, 'is_admin': current_app.user.is_admin()})
            # else: error already logged (maybe session file not writable)

        return {'errmsg': 'not able to log in; check server\'s log'}, 401
