Database Concept
================

Workflow
^^^^^^^^

Here you learn how you can create you database which will be accessed later from a web application. Follow these steps
as the first task in your project:

.. comment
   graph:: foo
   "bar" -- "baz";

.. blockdiag::
   :desctable:

   blockdiag {
       orientation = portrait

       // http://blockdiag.com/en/blockdiag/examples.html
       default_fontsize = 13;  // default value is 11

       // Set node metrix
       node_width = 300;  // default value is 128
       node_height = 50;  // default value is 40

       A [label = "Clarify the requirements"];
       B [label = "Create the SQL database"];
       C [label = "Export the SQL structure"];
       D [label = "Extract structure with extractsql.py"];
       E [label = "You've got the db_spec.json :)"];
       F [label = "Configure database server"];
       G [label = "Running SQL server"];

       A -> B -> C -> D -> E;
       C -> F -> G;

       A [description = "This is maybe the most difficult part: what has to be stored in the database?"];
       B [description = "Use for instance the MySQL Workbench tool which is used for this project. If you use something else expect some work in the *extractsql.py* tool."];
       C [description = "You have to generate the \*.sql command file which you use to create all the tables."];
       D [description = "This little script extracts all the fields from all tables and builds a JSON file."];
       E [description = "This database specification file also contains important attributes like the data type or if it could be NULL or not. It is used by the Python server."];
       F [description = "Create/configure the database on the server - for instance with the MySQL Workbench."];
       G [description = "Your database server is up and running. You have read and write access to it."];
   }

Notes about MySQL Workbench
^^^^^^^^^^^^^^^^^^^^^^^^^^^
* You can model your database with MySQL Workbench and let the database run on a MariaDB server because it's a fork of MySQL. MariaDB is shipped directly with many NAS systems.
* How you get the \*.sql command file once you have finished all the tables:
   1. Save the project
   2. Go to menu File > Export > Forward Engineer SQL CREATE Script...
   3. Enter the script file name in "Output SQL Script File:", for instance "db-<DATE>.sql" with the current date in the name.
      Save it in the project's "db" folder where also the JSON will be placed in.
   4. No options must be set in the dialog ("> Next")
   5. Only export the table objects, not views etc. ("> Next")
   6. Review the SQL script which will be saved. All the MySQL specific things will be ignored by the later *extractsql.py* script.
* How you can configure the database on the SQL server:
   1. Create a user account on the SQL server. This is a step which maybe must be done on the server's admin interface.
   2. (MySQL Workbench) Menu Database > Connect to Database
   3. Select the stored connection or create a new connection to the server. In every case you need admin permissions for the database schema you want to create.
   4. Now you're connected to the SQL server but you don't have your database loaded yet. Exactly said you have to create schema containing multiple tables.
   5. File > Open SQL Script > select the previously saved file "db-<DATE>.sql"
   6. Execute all the commands in this script.
   7. If you refresh the schemas on the left dock window you should see newly created schema with all the tables.
   8. Enjoy - you're done!

Other Databases?
^^^^^^^^^^^^^^^^
Is it possible to use other databases than MySQL/MariaDB? Here are some thoughts:

* Principally you could use every database which is supported by the `SQLAlchemy Engine`_.
* The *extracsql.py* script is made very simple and only parses the MySQL Workbench output correctly. If you want to use
  an other database improve the script and let it flow back please.
* In the end, you only need a correct *db_spec.json* file which can be written by hand easily.
* The Python UnitTest works with temporary SQlite databases - so this is an option too.

.. _SQLAlchemy Engine: https://docs.sqlalchemy.org/en/13/core/engines.html
