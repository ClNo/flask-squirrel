# This is the main runner which is used for local development and nginx environment (uwsgi),
# but not for testing (pytest).

from flask_squirrel.startup import flask_app

if __name__ == '__main__':
    flask_app.main(True)
else:
    # for nginx environment (uwsgi)
    flask_app.main(False)
