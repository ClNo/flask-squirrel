import datetime
import logging

from flask import Blueprint
from flask_restful import Api

import flask_squirrel
from sqlalchemy import create_engine, Table
import sys

log = logging.getLogger('backend')
log.level = logging.DEBUG


def open_create_db(sql_file, db_uri):
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


def on_after_config_loaded(app):
    open_create_db(app.config['db_creation_commands'], app.config['db_uri'])


def create_initial_db(app):
    # see help at https://docs.sqlalchemy.org/en/13/orm/extensions/automap.html
    User = app.config['db_base'].classes.users
    Supplier = app.config['db_base'].classes.suppliers
    Project = app.config['db_base'].classes.projects
    Ordering = app.config['db_base'].classes.orderings

    from sqlalchemy.orm import Session
    session: Session = Session(app.config['db_connect'])
    users_count = session.query(User).count()
    if users_count > 1:
        # todo: log info!
        return

    # create some initial data to work with
    user1 = User(username='u1', firstname='Fred', lastname='Fish', authentication_level=10, state='active',
                 credential_hash=flask_squirrel.util.session_auth.User.calc_hash_password('abc'))
    user2 = User(username='u2', firstname='John', lastname='Test', authentication_level=0, state='active',
                 credential_hash=flask_squirrel.util.session_auth.User.calc_hash_password('def'))
    user3 = User(username='u3', firstname='Lance', lastname='Armstrong', authentication_level=0, state='inactive',
                 credential_hash=flask_squirrel.util.session_auth.User.calc_hash_password('ghi'))

    supplier1 = Supplier(name='Supplier A')
    supplier2 = Supplier(name='Supplier B')

    project1 = Project(name='Project 1', comment='Project comment 1', project_state='running',
                       date_started=datetime.datetime.fromisoformat('2020-01-01'), date_finished=None)
    project2 = Project(name='Project 2', comment='Neverending project', project_state='running',
                       date_started=datetime.datetime.fromisoformat('2015-07-01'), date_finished=None)
    project3 = Project(name='Project 3', comment='Finished project', project_state='finished',
                       date_started=datetime.datetime.fromisoformat('2012-10-01'),
                       date_finished=datetime.datetime.fromisoformat('2018-02-10'))

    from sqlalchemy.orm import Session
    session: Session = Session(app.config['db_connect'])
    session.add_all([user1, user2, user3])
    session.add_all([supplier1, supplier2])
    session.add_all([project1, project2, project3])
    session.commit()

    ordering1 = Ordering(order_nameid='20-0001', idsupplier=supplier1.idsupplier, material='Cables AWG 21',
                         idproject=project1.idproject, idemployee_ordered=user1.iduser, order_state='ordered',
                         date_ordered=datetime.datetime.fromisoformat('2020-04-04'),
                         date_invoice_planned=datetime.datetime.fromisoformat('2020-05-04'),
                         date_planned=datetime.datetime.fromisoformat('2020-04-12'),
                         invoice='1300.50', comment='delayed')
    ordering2 = Ordering(order_nameid='20-0005', idsupplier=supplier1.idsupplier, material='Gear unit 1:37 ABC',
                         idproject=project1.idproject, idemployee_ordered=user1.iduser, order_state='invoiced',
                         date_ordered=datetime.datetime.fromisoformat('2020-02-02'),
                         date_invoice_planned=datetime.datetime.fromisoformat('2020-03-04'),
                         date_planned=datetime.datetime.fromisoformat('2020-02-10'),
                         date_delivered=datetime.datetime.fromisoformat('2020-02-08'),
                         date_invoiced_done=datetime.datetime.fromisoformat('2020-04-07'),
                         invoice='53390.00', comment=None)
    ordering3 = Ordering(order_nameid='17-0002', idsupplier=supplier2.idsupplier, material='Plates I345',
                         idproject=project2.idproject, idemployee_ordered=user3.iduser, order_state='invoiced',
                         date_ordered=datetime.datetime.fromisoformat('2017-02-02'),
                         date_invoice_planned=datetime.datetime.fromisoformat('2017-03-04'),
                         date_planned=datetime.datetime.fromisoformat('2017-02-10'),
                         date_delivered=datetime.datetime.fromisoformat('2017-02-08'),
                         date_invoiced_done=datetime.datetime.fromisoformat('2017-04-07'),
                         invoice='349.55', comment=None)
    ordering4 = Ordering(order_nameid='15-0003', idsupplier=supplier1.idsupplier, material='Drive shaft d55.5',
                         idproject=project3.idproject, idemployee_ordered=user2.iduser, order_state='invoiced',
                         date_ordered=datetime.datetime.fromisoformat('2015-02-02'),
                         date_invoice_planned=datetime.datetime.fromisoformat('2015-03-04'),
                         date_planned=datetime.datetime.fromisoformat('2015-02-10'),
                         date_delivered=datetime.datetime.fromisoformat('2016-02-08'),
                         date_invoiced_done=datetime.datetime.fromisoformat('2016-04-07'),
                         invoice='2349.05', comment=None)

    session.add_all([ordering1, ordering2, ordering3, ordering4])
    session.commit()


if __name__ == '__main__':
    hooks = {
        'after_config_loaded': on_after_config_loaded
    }
    app = flask_squirrel.create_app('orderings-config.json', hooks=hooks)

    # provide web app (html/js/css)
    frontend = Blueprint('orderings', __name__, static_folder='frontend', static_url_path='/orderings')
    app.register_blueprint(frontend)

    # provide upload directory to be accessed as URL
    upload_dir = Blueprint('upload_dir', __name__, static_folder=app.config['upload_dir'], static_url_path=app.config['file_url_path'])
    app.register_blueprint(upload_dir)

    # provide archive directory to be accessed as URL
    upload_dir = Blueprint('archive_dir', __name__, static_folder=app.config['archive_dir'], static_url_path=app.config['archive_url_path'])
    app.register_blueprint(upload_dir)

    from flask.logging import default_handler
    app.logger.setLevel(logging.INFO)
    log.addHandler(default_handler)
    log.setLevel(logging.INFO)

    # provide the Config API to be accessed as URL
    # the api object is a flask_restful manager class which helps to provide and process JSON data over HTTP requests
    api = Api(app)
    log.info('Adding resource /{0}/config-api to routes...'.format(app.config['api_path']))
    from config_api import ConfigApi
    api.add_resource(ConfigApi, '/{0}/config-api'.format(app.config['api_path']), endpoint='config-api')

    log.info('Adding resource /{0}/upload-filelist to routes...'.format(app.config['api_path']))
    table_name = 'documents'
    from flask_squirrel import DirManager
    api.add_resource(DirManager, '/{0}/upload-filelist'.format(app.config['api_path']), endpoint='upload-filelist',
                     resource_class_kwargs={'managed_dir': app.config['upload_dir'], 'table_name': table_name})

    create_initial_db(app)

    app.run(host=app.config['listening_ip'], port=app.config['listening_port'])
