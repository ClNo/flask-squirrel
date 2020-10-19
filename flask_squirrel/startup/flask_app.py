import traceback

from flask import Flask, Blueprint
from flask_restful import Api

from flask_squirrel import DbTable, LoginTokenApi
from flask_squirrel import ResourceViewSpec

import argparse
import json
import os
import sys

from flask_cors import CORS
import sqlalchemy
import sqlalchemy.ext.automap

import logging
import locale

log = logging.getLogger('restserver')
log.level = logging.DEBUG

ALTERNATIVE_CONFIG_FILE = 'rest-db-config.json'
DOCROOT_PATH = 'docroot'
DEFAULT_STATIC_PATH = os.path.join(os.getcwd(), DOCROOT_PATH)
API_PATH = None


EXPECTED_CONFIG_KEYS = [
    {'name': 'version', 'type': 'string'},
    {'name': 'listening_ip', 'type': 'string'},
    {'name': 'listening_port', 'type': 'int'},
    {'name': 'api_path', 'type': 'string'},
    {'name': 'db_uri', 'type': 'string'},
    {'name': 'db_spec', 'type': 'file-json'},
    {'name': 'customview_spec', 'type': 'file-json'},
    {'name': 'translation_spec', 'type': 'file-json'},
    {'name': 'create_not_existing_dirs', 'type': 'bool'},
    {'name': 'upload_dir', 'type': 'path'},
    {'name': 'archive_dir', 'type': 'path'},
    {'name': 'session_dir', 'type': 'path'},
    {'name': 'flask-debug', 'type': 'bool'}
]


def parse_config_file_check(config_filename):

    current_filename = config_filename
    create_not_existing_dirs = False
    try:
        if not config_filename:
            print('Error: no JSON configuration file given')
            print()
            sys.exit(1)

        with open(config_filename, 'r') as f:
            config_dict = json.load(f)

        # first check for key which are not available but are mandatory
        for conf in EXPECTED_CONFIG_KEYS:
            if conf['name'] not in config_dict:
                raise Exception('Expected key {0} not in set in config file'.format(conf['name']))

        for conf in EXPECTED_CONFIG_KEYS:
            if conf['type'] == 'file-json':
                current_filename = config_dict[conf['name']]
                with open(current_filename, 'r') as f:
                    loaded_dict = json.load(f)
                # replace the filename by its JSON content
                config_dict[conf['name']] = loaded_dict

            elif conf['type'] == 'path':
                current_filename = config_filename
                if not os.path.isdir(config_dict[conf['name']]):
                    if create_not_existing_dirs:
                        os.makedirs(config_dict[conf['name']])
                    else:
                        raise Exception('Expected directory not existing: {0}'.format(config_dict[conf['name']]))

            elif conf['name'] == 'create_not_existing_dirs':
                create_not_existing_dirs = config_dict[conf['name']]

    except Exception as e:
        print('Error parsing JSON file \'{0}\': {1}'.format(current_filename, e))
        print()
        traceback.print_exc(file=sys.stdout)
        print()
        sys.exit(2)

    return config_dict


def create_app(config_filename=None, additional_config=None, hooks=None):
    """Create and configure an instance of the Flask application."""

    from flask.logging import default_handler
    log.addHandler(default_handler)
    log.setLevel(logging.INFO)

    # first handle the configuration file before the flask app will be created
    if not config_filename:
        config_filename = ALTERNATIVE_CONFIG_FILE
        print('Using default config file: {0}'.format(config_filename))

    custom_config = parse_config_file_check(config_filename)

    if additional_config:
        custom_config.update(additional_config)

    global API_PATH
    API_PATH = custom_config['api_path']

    # now create the flask app object
    app = Flask(__name__, static_folder=DEFAULT_STATIC_PATH)
    app.logger.setLevel(logging.INFO)

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
    )

    # copy the custom config into the flask app's config (app.config[<key>]) for using it in every route
    for key in custom_config:
        if key in app.config:
            log.info('Overriding config item {0}: {1} -> {2}'.format(key, app.config[key], custom_config[key]))
    app.config.update(custom_config)

    # set the config's flask static path insted of the original one
    if 'static_flask_filepath' in app.config:
        app.static_folder = app.config['static_flask_filepath']

    if 'LC_TIME' in app.config:
        try:
            locale.setlocale(locale.LC_TIME, app.config['LC_TIME'])
        except Exception as e:
            log.error('Cannot set language LC_TIME={0}: {1}'.format(app.config['LC_TIME'], e))

    if hooks and 'after_config_loaded' in hooks:
        # call first hook after loading configuration
        hooks['after_config_loaded'](app)

    # CORS is an access protection for browsers. Here we just open it to allow the browser accessing data from
    # different hosts than just from this flask server.
    CORS(app)

    # the api object is a flask_restful manager class which helps to provide and process JSON data over HTTP requests
    api = Api(app)

    # ensure the instance folder exists
    # try:
    #     print('Create instance paths: ', app.instance_path)
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # if we're in pytest mode, the temporary database should already have been created
    if 'TEST_DATABASE' in app.config:
        app.config['db_uri'] = '{0}{1}'.format(app.config['db_uri'], app.config['TEST_DATABASE'])
        msg = 'Creating test database at {0}'.format(app.config['db_uri'])
        print(msg)
        log.warning(msg)

    # create the database connector and store it into the flask app config
    db_connect: sqlalchemy.Engine = sqlalchemy.create_engine(app.config['db_uri'])  # not supported here: read_only=args.read_only)
    app.config['db_connect']: sqlalchemy.engine.Engine = db_connect
    app.config['db_fail'] = False
    app.config['db_meta']: sqlalchemy.MetaData = sqlalchemy.MetaData()
    app.config['db'] = {}
    try:
        # now create SQLAlchemy ORM reflection objects (= read ORM from the existing DB)
        app.config['db_meta'].reflect(bind=app.config['db_connect'])
        for table_object in app.config['db_meta'].sorted_tables:
            app.config['db'][str(table_object)]: sqlalchemy.Table = table_object
        app.config['db_base']: sqlalchemy.ext.automap = sqlalchemy.ext.automap.automap_base(metadata=app.config['db_meta'])
        app.config['db_base'].prepare()
    except sqlalchemy.exc.SQLAlchemyError as e:
        app.config['db_fail'] = True
        app.config['db_fail_err'] = 'SQL code:{0} message:{1}'.format(e.orig.args[0], e.orig.args[1])

    app.config['current_lang'] = 'en'      # default language

    from flask_squirrel.table.db_placeholder_parser import DbPlaceholderParser
    app.config['db_placeholder_parser'] =\
        DbPlaceholderParser(app.config['customview_spec'], app.config['translation_spec'], app.config['db_spec'],
                            app.config['db'], db_connect)

    from flask_squirrel.util.view_spec_generator import ViewSpecGenerator
    view_spec_generator = ViewSpecGenerator(app.config['customview_spec'], app.config['translation_spec'],
                                            app.config['db_spec'])
    app.config['view_spec_generator'] = view_spec_generator

    log.info('Adding resource /{0}/resource-view-spec to routes...'.format(API_PATH))
    api.add_resource(ResourceViewSpec, '/{0}/resource-view-spec'.format(API_PATH), endpoint='resource-view-spec')

    for table_name in app.config['db_spec']:
        log.info('Adding table /{0}/{1} to routes...'.format(API_PATH, table_name))
        api.add_resource(DbTable, '/{0}/{1}'.format(API_PATH, table_name), endpoint='api-{0}'.format(table_name),
                         resource_class_kwargs={'table_name': table_name})

    if 'upload_dir' in app.config:
        # optional upload route
        log.info('Adding resource /{0}/upload to routes...'.format(API_PATH))
        from flask_squirrel.util import uploadroute
        app.register_blueprint(uploadroute.bp, url_prefix='/{0}'.format(API_PATH))

    if ('static_directory' in app.config) and ('static_url' in app.config):
        # provide web app (html/js/css)
        frontend = Blueprint(app.config['static_url'], __name__, static_folder=app.config['static_directory'],
                             static_url_path='/{0}'.format(app.config['static_url']))
        app.register_blueprint(frontend)

    log.info('Adding resource /{0}/login-token to routes...'.format(API_PATH))
    # Set an initial login attribute for handling of verification in verify_password
    if 'login-token' not in app.config['customview_spec']:
        app.config['customview_spec']['login-token'] = {}
    app.config['customview_spec']['login-token']['_attributes'] = ['login_route']
    api.add_resource(LoginTokenApi, '/{0}/login-token'.format(API_PATH), endpoint='login-token')

    # Now make sure that an admin user exists. The initial UN/PW is in the config file and can be changed.
    from flask_squirrel.util import session_auth
    session_auth.User.check_initial_user(app)
    app.user = None

    return app


class ArgumentParserError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def main(run_app, config_filename=None):
    """Main entry point for script."""

    if not config_filename:
        parser = ThrowingArgumentParser(description='Provide a RESTful API service from the order database.')
        parser.add_argument('config_file', help='JSON configuration file', type=argparse.FileType('r'))
        args = parser.parse_args()

        app = create_app(args.config_file.name)

    else:
        app = create_app(config_filename)

    if 'flask-debug' in app.config:
        do_debug = app.config['flask-debug']
    else:
        do_debug = False

    if run_app:
        if app.config['listening_ip'] and app.config['listening_port']:
            app.run(host=app.config['listening_ip'], port=app.config['listening_port'], debug=do_debug)
        else:
            # expect a nginx environment
            app.run(debug=do_debug)
