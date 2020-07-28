Custom View Specification
=========================

There are relations and conditions which cannot be automatically generated out of the database - or at least which are
not implemented yet. That information must be given manually in this file called *db_customview_spec.json*.

For each table there can optionally be given some additional information. So the first keyword which occurs is always
the table name.

Hidden Tables
-------------

Tables which should not be presented to the user on the web app should be marked as hidden - for instance:

.. code-block:: json
    :linenos:

    {
        "config": {
            "_attributes": ["hidden"]
        }
    }

In this example, the table named 'config' is marked to be hidden with the sub key "_attributes" and the value "hidden".

Relation to Other Tables
------------------------

Relations to tables are called *foreign keys* and are also abbreviated *FK*. Foreign keys are typically just a number
which is an identifier to the *primary key (PK)* of the other table which it is pointing to. So if the user would enter
the correct number he could set for instance the customer of the ordering.

But the user does not want to enter the correct number (primary key) but for instance the name of the customer. So for
each relation to an other table you have to specify *what* should be shown - the first name and the family name?

In the following example you can see three relations from the table *orderings* to *suppliers*, *projects* and
*employees*:

.. code-block:: json
    :linenos:

    {
        "orderings": {
            "idsupplier": {"ref_text": ["suppliers.name"]},
            "idproject": {"ref_text": ["projects.name"]},
            "idemployee_ordered": {"ref_text": ["employees.abbr"]}
    	}
    }

So at the end we have three mappings in this example:

========= ================== =============== ============
Table     Column             Mapped to Table Shown Column
========= ================== =============== ============
orderings idsupplier         suppliers       name
orderings idproject          projects        name
orderings idemployee_ordered employees       abbr
========= ================== =============== ============

Insertion of new Fields
-----------------------

.. todo:: Document field insertion! link / connected_file / file_path

.. code-block:: json

    {
	    "documents": {
		    "filename": {"link":  "{ARCHIVE_URL_PATH}", "connected_file": true, "file_path": "{ARCHIVE_DIR}"}
        }
    }

Conclusion
----------

1. Mark all tables which are not shown on the web app as "hidden"
2. For all foreign keys the related table and a column must be configured. Otherwise the user has to enter a number for
   the foreign key.
