Database Specification
======================

What is the file db_spec.json?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This file contains the structure of the database with all important attributes like the data type or if it could be NULL
or not. It is used by the Python server to do the following tasks:

1. Generate SQL queries and also follow the dependencies (related tables)
2. Generate some view specifications for the user entries. Something which is "not-null" must be entered in input form.

The follwong JSON structure is a *db_spec.json* of a simple database structure which has been designed with the MySQL
Workbench and has been exported like described in the previous page :doc:`database`.

Each main key like "suppliers" or "projects" describe a database table with the same name.

.. code-block:: json
    :linenos:

    {
        "suppliers": {
            "columns": [
                {
                    "name": "idsupplier",
                    "type": "uint",
                    "func": "primarykey",
                    "not-null": true,
                    "auto-increment": true
                },
                {
                    "name": "name",
                    "type": "string",
                    "func": "value",
                    "type-details": "200",
                    "not-null": true
                }
            ]
        },
        "projects": {
            "columns": [
                {
                    "name": "idproject",
                    "type": "uint",
                    "func": "primarykey",
                    "not-null": true,
                    "auto-increment": true
                },
                {
                    "name": "name",
                    "type": "string",
                    "func": "value",
                    "type-details": "200",
                    "not-null": true
                },
                {
                    "name": "comment",
                    "type": "string",
                    "func": "value",
                    "type-details": "200"
                }
            ]
        },
        "employees": {
            "columns": [
                {
                    "name": "idemployee",
                    "type": "uint",
                    "func": "primarykey",
                    "not-null": true,
                    "auto-increment": true
                },
                {
                    "name": "abbr",
                    "type": "string",
                    "func": "value",
                    "type-details": "10",
                    "not-null": true
                },
                {
                    "name": "firstname",
                    "type": "string",
                    "func": "value",
                    "type-details": "60",
                    "not-null": true
                },
                {
                    "name": "lastname",
                    "type": "string",
                    "func": "value",
                    "type-details": "60",
                    "not-null": true
                },
                {
                    "name": "authentication_level",
                    "type": "int",
                    "func": "value",
                    "not-null": true
                },
                {
                    "name": "state",
                    "type": "enum",
                    "func": "value",
                    "type-details": [
                        "active",
                        "inactive"
                    ],
                    "not-null": true
                }
            ]
        },
        "orderings": {
            "columns": [
                {
                    "name": "idordering",
                    "type": "uint",
                    "func": "primarykey",
                    "not-null": true,
                    "auto-increment": true
                },
                {
                    "name": "order_nameid",
                    "type": "string",
                    "func": "value",
                    "type-details": "100",
                    "not-null": true
                },
                {
                    "name": "idsupplier",
                    "type": "uint",
                    "func": "foreignkey",
                    "not-null": true,
                    "reference": "suppliers.idsupplier"
                },
                {
                    "name": "idproject",
                    "type": "uint",
                    "func": "foreignkey",
                    "not-null": true,
                    "reference": "projects.idproject"
                },
                {
                    "name": "idemployee_ordered",
                    "type": "uint",
                    "func": "foreignkey",
                    "not-null": true,
                    "reference": "employees.idemployee"
                },
                {
                    "name": "order_state",
                    "type": "enum",
                    "func": "value",
                    "type-details": [
                        "ordered",
                        "confirmed",
                        "delivered",
                        "invoiced"
                    ],
                    "not-null": true
                },
                {
                    "name": "date_invoiced_done",
                    "type": "date",
                    "func": "value"
                },
                {
                    "name": "invoice",
                    "type": "decimal",
                    "func": "value",
                    "type-details": [
                        "8",
                        "2"
                    ],
                    "not-null": true
                },
                {
                    "name": "comment",
                    "type": "string",
                    "func": "value",
                    "type-details": "200"
                }
            ]
        },
        "documents": {
            "columns": [
                {
                    "name": "iddocument",
                    "type": "uint",
                    "func": "primarykey",
                    "not-null": true,
                    "auto-increment": true
                },
                {
                    "name": "name",
                    "type": "string",
                    "func": "value",
                    "type-details": "100",
                    "not-null": true
                },
                {
                    "name": "filename",
                    "type": "string",
                    "func": "value",
                    "type-details": "1000",
                    "not-null": true
                },
                {
                    "name": "type",
                    "type": "enum",
                    "func": "value",
                    "type-details": [
                        "undefined",
                        "order",
                        "orderconfirmation",
                        "delivery",
                        "invoice"
                    ],
                    "not-null": true
                },
                {
                    "name": "filedate",
                    "type": "date",
                    "func": "value",
                    "not-null": true
                },
                {
                    "name": "idemployee_added",
                    "type": "uint",
                    "func": "foreignkey",
                    "not-null": true,
                    "reference": "employees.idemployee"
                },
                {
                    "name": "idordering",
                    "type": "uint",
                    "func": "foreignkey",
                    "not-null": true,
                    "reference": "orderings.idordering"
                },
                {
                    "name": "comment",
                    "type": "string",
                    "func": "value",
                    "type-details": "200"
                }
            ]
        }
    }

JSON description
^^^^^^^^^^^^^^^^

The main elements of *db_spec.json* are:

1. The table names; each table is described at the top level of the structure.
2. "columns": a list all attributes for one field

============== ============== ==========================================================================================
Column key     Values, Types  Description
============== ============== ==========================================================================================
name           string
type           | uint
               | string
               | decimal
func           | value
               | primarykey
               | foreignkey
not-null
reference
type-details
auto-increment
============== ============== ==========================================================================================


.. todo:: db_spec.json documentation!
