Flask-Squirrel
==============

The squirrel fetches your nuts and places them in a storage. So Flask-Squirrel is a database backend which provides your database over a REST API and also allows your business logic.

Besides the Python backend there is also a JavaScript frontend which is a bit raw but shows the pre-configured tables in the browser in an easy way.

.. note::

   Flask-Squirrel is in testing stage - your contributions are welcome!


.. note::

   This doc is under construction. Give me some time to build a good tutorial and design description.

.. note::

   Check the tests to see how you can use REST API for now. Also take a look at the "Orderings" example for Ajax calls.

   
Design Goals
------------

There are may alternatives for doing this, but there are some important differences which makes it unique:

- No HTML generation; access the database and your custom routes via a REST API (JSON content).
- Goal: both, the frontend and the backend are replaceable and not directly dependent of each other. Each part can separately be implemented and tested.
- Nevertheless: the `jQuery Datatables <https://datatables.net>`_ component is used in the frontend which requires a `specific <https://editor.datatables.net/manual/server>`_ JSON data structure which must be provided by the backend. Therefore a specific datatables serializer is implemented.
- A simple token mechanism has been implemented: authenticate to a specific login route in the basic or digest authentication mode then you get a token which is used to access all the nuts you want (read and/or write).
- Some view specifications will also be provided to the frontend so a generic JavaScript component can be used to edit the data instead of writing a frontend component for everything. For instance, not all fields should be editable so you can specify this in configuration item.
- An upload route is provided for simple file handling (e.g. store project docs in relation to the project table).
- The squirrel is is extendable for any business logic - write your own Python modules and connect it as Flask routes/APIs. The SQLAlchemy database handler will be passed to your custom modules and grants you an easy access to your tables.
- There are some JavaScript examples for the frontend you can use, but note that used Datatables is commercial (but it's worth every penny!).
- Currently there is no database creation; do it with your favorite DB tool and pass the SQL file to a conversion tool which builds a JSON specification used by the backend.

The bottom line is: if you just have some tables which are simply related to each other you don't have to program anything - it's just a matter of configuration. Your business logic can be appended as you want.

.. blockdiag::
   :desctable:

   blockdiag {
       orientation = portrait;

       default_fontsize = 12;  // default value is 11

       // Set node metrix
       node_width = 200;  // default value is 128
       node_height = 40;  // default value is 40

       A [label = "Browser Frontend"];
       B [label = "Flask, Flask-Squirrel, Business Logic, Config"];
       C [label = "database", shape = "flowchart.database"];

       A -> B -> C;
   }
