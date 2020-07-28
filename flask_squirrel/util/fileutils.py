import datetime
import os


def get_file_list(walk_dir_name, file_url_path):
    files = []
    rowcnt = 0
    for dirname, subdir_list, file_list in os.walk(walk_dir_name):
        for fname in file_list:
            abs_file_path = os.path.join(walk_dir_name, fname)

            fstat = os.stat(abs_file_path)
            mtime = os.path.getmtime(abs_file_path)
            mtime_ts = datetime.datetime.fromtimestamp(mtime)
            mtime_str = mtime_ts.isoformat()[:19]   # this only works for Python 3.6+: timespec='seconds')

            size = fstat.st_size
            sizestr = '{0} B'.format(size)
            if int(size / 1024) >= 10:
                sizestr = '{0} KB'.format(int(size / 1024))
            if int((size / 1024) / 1024) >= 10:
                sizestr = '{0} MB'.format(int((size / 1024) / 1024))

            files.append({'DT_RowId': rowcnt, 'name': fname, 'size_b': size, 'size_hr': sizestr,
                          'mtime': mtime_str, 'link': '{0}/{1}'.format(file_url_path, fname)})
            rowcnt += 1
    return files


def get_valid_filename(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    see: https://docs.djangoproject.com/en/2.1/_modules/django/utils/text/#slugify
    """
    value = str(value)
    import unicodedata
    value = unicodedata.normalize('NFKD', value)
    import re
    value = re.sub(r'[^\w\s._-]', '', value).strip()
    return re.sub(r'[\s]+', '_', value)
