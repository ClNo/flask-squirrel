# Notes about testing:
# - the original guide does not work!
#   http://flask.pocoo.org/docs/1.0/testing/
# - the tutorial code example ist working well:
#   https://github.com/pallets/flask/tree/master/examples/tutorial
# - therefore the code variant as been used and not the guide variant!

import json
import os
import tempfile
import pytest
import shutil
import sys
import traceback

from sqlalchemy import create_engine
from werkzeug import test

sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))
from flask_squirrel.startup.flask_app import create_app


TEST_CONFIG_FILE = 'tests/data/test-db-config.json'


def prepare_test_conditions(config_filename, test_database_filename):

    current_filename = config_filename
    try:
        if not config_filename:
            print('Error: no JSON configuration file given')
            sys.exit(1)

        with open(config_filename, 'r') as f:
            config_dict = json.load(f)

        upload_dir: str = config_dict['upload_dir']
        archive_dir: str = config_dict['archive_dir']
        session_dir: str = config_dict['session_dir']

        if (not upload_dir.startswith('/tmp')) or (not archive_dir.startswith('/tmp')):
            print('Error: test directory is not in /tmp')
            sys.exit(2)

        if os.path.isdir(upload_dir):
            shutil.rmtree(upload_dir)
        os.makedirs(upload_dir)

        if os.path.isdir(archive_dir):
            shutil.rmtree(archive_dir)
        os.makedirs(archive_dir)

        if os.path.isdir(session_dir):
            shutil.rmtree(session_dir)
        os.makedirs(session_dir)

        if 'sqlite:' not in config_dict['db_uri']:
            print('Error: only SQlite database for testing accepted')
            sys.exit(2)

        if 'db_test_creation' not in config_dict:
            print('Error: key \'db_test_creation\' not in test configuration')
            sys.exit(2)

        db_uri = '{0}{1}'.format(config_dict['db_uri'], test_database_filename)

        create_testing_db(config_dict['db_test_creation'], db_uri)

    except Exception as e:
        print('Error parsing JSON file \'{0}\' and preparing test conditions: {1}'.format(current_filename, e))
        traceback.print_exc(file=sys.stdout)
        print()
        sys.exit(2)

    return config_dict


def create_testing_db(sql_file, db_uri):
    db_connect = create_engine(db_uri)
    with open(sql_file, 'r') as f:
        sql_cmd_list = f.readlines()

    try:
        conn = db_connect.connect()
        collect_line = ''
        for sql_cmd in sql_cmd_list:
            # collect multiple lines as long as the trailing ';' has been reached
            if sql_cmd.strip().startswith('--'):
                continue
            collect_line += sql_cmd
            if ';' in sql_cmd:
                # line finished, execute it
                collect_line = collect_line.replace('\n', '')

                # print(collect_line)
                result = conn.execute(collect_line)
                # print(result)
                # print()
                collect_line = ''
        # result_rows = result.fetchall()
        # log.debug(result_rows)
        # pass
    except Exception as e:
        print('SQL database creation failed: {0}'.format(e))
        sys.exit(3)


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""

    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    prepare_test_conditions(TEST_CONFIG_FILE, db_path)

    # create the app with common test config
    app = create_app(TEST_CONFIG_FILE, {"TESTING": True, "TEST_DATABASE": db_path})

    # create the database and load test data
    # with app.app_context():
    #     init_db()
    #     get_db().executescript(_data_sql)

    yield app

    # close and remove the temporary database
    os.close(db_fd)
    # let it remain for later checks: os.unlink(db_path)


@pytest.fixture
def client(app) -> test.Client:
    """A test client for the app."""
    from tests.client_app_config import client_config
    import copy
    if not client_config.db_spec:
        client_config.db_spec = copy.deepcopy(app.config['db_spec'])
    if not client_config.customview_spec:
        client_config.customview_spec = copy.deepcopy(app.config['customview_spec'])
    if not client_config.translation_spec:
        client_config.translation_spec = copy.deepcopy(app.config['translation_spec'])
    if not client_config.api_path:
        client_config.api_path = app.config['api_path']
    if not client_config.default_admin_user:
        client_config.default_admin_user = copy.deepcopy(app.config['default_admin_user'])
    if not client_config.session_dir:
        client_config.session_dir = app.config['session_dir']
    if not client_config.upload_dir:
        client_config.upload_dir = app.config['upload_dir']
    if not client_config.archive_dir:
        client_config.archive_dir = app.config['archive_dir']
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
