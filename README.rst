Flask-Squirrel
==============

The squirrel collects your nuts and stores them into your SQL database so it is a REST API which accesses your database.
It is based on Flask, Flask-RESTful and Flask-SQLAlchemy.

Major benefits:

- The database data is formatted as a JSON which can be used by the great jQuery library datatables.
- Multilanguage
- Allows custom business logic
- Basic document upload support
- No HTML is generated - REST API only


First Steps to Run the Demo
---------------------------

There is a small document management example to show how you can use Flask-Squirrel. The goal is to upload a document on a server
and assign it to an internal ordering of material a small company uses for its projects.

The following steps run in Linux; for Windows or Mac you should adapt some paths in the configuration.

.. note::

   The demo needs at least Python 3.7 because of the function datetime.datetime.fromisoformat() for the initial DB creation.
   Flask-Squirrel itself also works with Python 3.6.


.. code-block:: shell
   :description: Project Setup

   python3 --version
   # should be at least 3.7 for running the demo

   # go into your project directory
   git clone https://github.com/ClNo/flask-squirrel.git
   cd flask-squirrel
   
   python3 -m venv venv    # if you have multiple versions: call python3.7 ..
   source venv/bin/activate
   pip install --upgrade pip
   python setup.py develop


.. code-block:: shell
   :description: Run the Demo

   cd examples/orderings
   python3 backend.py


You should get the following output of the SQL backend:
   
.. code-block::
   :description: Backend Output

   INFO in flask_app: Overriding config item SECRET_KEY: dev -> _5#y2LF4Q8z-\xec]/
   INFO in flask_app: Overriding config item SESSION_COOKIE_SAMESITE: None -> Lax
   INFO in flask_app: Overriding config item SESSION_COOKIE_SECURE: False -> True
   INFO in flask_app: Adding resource /orderings-api/resource-view-spec to routes...
   INFO in flask_app: Adding table /orderings-api/suppliers to routes...
   INFO in flask_app: Adding table /orderings-api/projects to routes...
   INFO in flask_app: Adding table /orderings-api/users to routes...
   INFO in flask_app: Adding table /orderings-api/orderings to routes...
   INFO in flask_app: Adding table /orderings-api/documents to routes...
   INFO in flask_app: Adding table /orderings-api/config to routes...
   INFO in flask_app: Adding resource /orderings-api/upload to routes...
   INFO in flask_app: Adding resource /orderings-api/login-token to routes...
   INFO in backend: Adding resource /orderings-api/config-api to routes...
   INFO in backend: Adding resource /orderings-api/upload-filelist to routes...
    * Serving Flask app "flask_squirrel.startup.flask_app" (lazy loading)
    * Environment: production
      WARNING: This is a development server. Do not use it in a production deployment.
      Use a production WSGI server instead.
    * Debug mode: on
    * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)

Now you can test the REST API with a tool like curl:

.. code-block:: shell
   :description: API Test 1

   $ curl 'http://127.0.0.1:5000/orderings-api/users?get=data_spec&version=1&lang=en'

The result contains the data but as well the table and table editor specification (argument "get=data_spec"):

.. code-block:: json
   :description: API Output

   {
       "data": [
           {
               "users": {
                   "iduser": 1,
                   "username": "admin",
                   "firstname": "John",
                   "lastname": "Test",
                   "credential_hash": "----------",
                   "authentication_level": 10,
                   "state": "active"
               },
               "DT_RowId": 1,
               "users_state": {
                   "name": "active"
               }
           },
           {
               "users": {
                   "iduser": 2,
                   "username": "u1",
                   "firstname": "Fred",
                   "lastname": "Fish",
                   "credential_hash": "----------",
                   "authentication_level": 10,
                   "state": "active"
               },
               "DT_RowId": 2,
               "users_state": {
                   "name": "active"
               }
           },
           {
               "users": {
                   "iduser": 3,
                   "username": "u2",
                   "firstname": "John",
                   "lastname": "Test",
                   "credential_hash": "----------",
                   "authentication_level": 0,
                   "state": "active"
               },
               "DT_RowId": 3,
               "users_state": {
                   "name": "active"
               }
           },
           {
               "users": {
                   "iduser": 4,
                   "username": "u3",
                   "firstname": "Lance",
                   "lastname": "Armstrong",
                   "credential_hash": "----------",
                   "authentication_level": 0,
                   "state": "inactive"
               },
               "DT_RowId": 4,
               "users_state": {
                   "name": "inactive"
               }
           }
       ],
       "options": {
           "users.state": [
               {
                   "label": "(State)",
                   "value": null
               },
               {
                   "label": "active",
                   "value": "active"
               },
               {
                   "label": "inactive",
                   "value": "inactive"
               }
           ]
       },
       "filters": null,
       "editor-filters": null,
       "translation": {}
   }

You can also access the interface in a browser with the URL http://127.0.0.1:5000/orderings/index.html

.. image:: demo-screenshot_1.png
   :target: Demo Viewer

If you have the DataTables Editor (download a trial) you are able to edit the table rows:
   
.. image:: demo-screenshot_2.png
   :target: Demo Editor