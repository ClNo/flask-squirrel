from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
import os

import logging

log = logging.getLogger('uploadroute')
log.level = logging.DEBUG

bp = Blueprint('uploadroute', __name__)


# @bp.route('/{0}/upload'.format(API_PATH), methods=['POST'])
@bp.route('/upload', methods=['POST', 'DELETE'])
def upload_file():
    if not current_app.config['upload_dir']:
        msg = 'No upload path specified'
        log.error(msg)
        return msg, 500

    upload_dir = current_app.config['upload_dir']

    if not os.path.isdir(upload_dir):
        msg = 'Upload path \'{0}\' does not exist'.format(upload_dir)
        log.error(msg)
        return msg, 500

    if request.method == 'POST':
        # also take a look at: https://www.programcreek.com/python/example/51528/flask.request.files
        filelist = request.files.getlist('file')
        if not filelist:
            filelist = request.files.getlist('file[0]')  # unclear behavior: why [0] ?
        log.info(filelist)
        return _upload(upload_dir, filelist)

    elif request.method == 'DELETE':
        # expected: 'HTTP_CONTENT_TYPE': 'application/x-www-form-urlencoded'
        try:
            del_filename = request.values['file']
        except Exception as e:
            msg = 'DELETE request with unexpected data format; try \'application/x-www-form-urlencoded\''
            log.error(msg)
            return {'success': False, 'error': msg}, 400, {'ContentType': 'application/json'}

        return _delete(upload_dir, [del_filename])  # single file expected

    msg = 'Not a POST or DELETE request to upload path! {0}'.format(request.method)
    log.error(msg)
    return {'success': False, 'error': msg}, 400, {'ContentType': 'application/json'}


def _upload(upload_dir, filelist):
    log.info('Upload request for files: {0}'.format(request.files))
    for f in filelist:
        filename = os.path.join(upload_dir, secure_filename(f.filename))
        f.save(filename)

        size = os.stat(filename).st_size
        sizestr = '{0} B'.format(size)
        if int(size / 1024) >= 10:
            sizestr = '{0} KB'.format(int(size / 1024))
        if int((size / 1024) / 1024) >= 10:
            sizestr = '{0} MB'.format(int((size / 1024) / 1024))

        log.info('File {0} saved: {1}'.format(filename, sizestr))

    return {'success': True}, 200, {'ContentType': 'application/json'}


def _delete(upload_dir, filelist):
    log.info('Request for deleting uploaded files: {0}'.format(request.files))

    for fn in filelist:
        filename = os.path.join(upload_dir, secure_filename(fn))

        try:
            os.remove(filename)
        except OSError as e:
            msg = 'Failed to delete file \'{0}\': {1}'.format(filename, e.strerror)
            log.error(msg)
            return {'success': False, 'error': msg}, 400, {'ContentType': 'application/json'}
    return {'success': True}, 200, {'ContentType': 'application/json'}
