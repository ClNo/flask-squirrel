Database Filter
===============

Filters can be done in two ways:
    1. Client side: filter the data received from the server.
    2. Server side: pass some filter data in the request and get only the data which is required.

Client side filter is done by the JavaScript table component itself and the server side filter is explained here.
Here, a concept of predefined filters is used which means it will be always the same WHERE-condition applied to the
SQL query. Look at the example configuration in ``db_customview_spec.json``:

.. code-block:: json
    :linenos:
    :emphasize-lines: 6,7,11,13,18,22

    {
        "orderings": {
            "idsupplier": {"ref_text": ["suppliers.name"]},
            "idproject": {"ref_text": ["projects.name"]},
            "idemployee_ordered": {"ref_text": ["employees.abbr"]},
            "_predefined_filters": {
                "projects-running": {
                    "base_table": "orderings", "base_column": "idproject",
                    "join_table": "projects", "join_column": "idproject",
                    "and_condition": "projects.project_state='running'",
                    "default": true
                },
                "projects-finished": {
                    "base_table": "orderings", "base_column": "idproject",
                    "join_table": "projects", "join_column": "idproject",
                    "and_condition": "projects.project_state='finished'"
                },
                "projects-all": {
                    "base_table": "orderings", "base_column": "idproject",
                    "join_table": "projects", "join_column": "idproject"
                },
                "orderings-last-3-years": {
                    "base_table": "orderings", "base_column": "idproject",
                    "join_table": "projects", "join_column": "idproject",
                    "and_condition": {
                        "sqlite": "orderings.date_ordered >= DATE('now', '-3 year')",
                        "mysql": "orderings.date_ordered >= DATE_SUB(CURRENT_DATE, INTERVAL 3 YEAR)"
                    }
                }
            },
            "_attributes": ["write_everyone"],
            "_translation": {
                "table_multi": {"en": "Orderings", "de": "Bestellungen"},
                "table_single": {"en":  "ordering", "de": "Bestellung"},
                "article": {"en":  "a", "de": "eine"}
            }
        }
    }

Note the default filter definition in the line 11 above: ``"default": true``.

The predefined filter needs some definitions in ``translation.json`` which will be transferred to the web app:

.. code-block:: json
    :linenos:
    :emphasize-lines: 29-32

	{
        "orderings": {
            "orderings": {"en": "Orderings", "de": "Bestellungen"},
            "idordering":  {"en": "ID", "de": "ID"},
            "idproject":  {"en": "Project", "de": "Projekt"},
            "idsupplier": {"en": "Supplier", "de": "Lieferant"},
            "order_nameid":  {"en": "Order number", "de": "Bestellnummer"},
            "material":  {"en": "Material", "de": "Material"},
            "order_state":  {"en": "Order state", "de": "Bestellstatus"},
            "order_state.ordered":  {"en": "ordered", "de": "bestellt"},
            "order_state.confirmed":  {"en": "confirmed", "de": "bestätigt"},
            "order_state.delivered":  {"en": "delivered", "de": "geliefert"},
            "order_state.invoiced":  {"en": "invoiced", "de": "verrechnet"},
            "idemployee_ordered":  {"en": "Who ordered", "de": "Wer bestellt"},
            "date_ordered":  {"en": "Date ordered", "de": "Bestelldatum"},
            "date_invoice_planned":  {"en": "Date invoice planned", "de": "Gepl. Rechnungsdatum"},
            "date_planned":  {"en": "Date planned", "de": "Gepl. Lieferdatum"},
            "date_delivered":  {"en": "Date delivered", "de": "Lieferdatum"},
            "date_invoiced_done":  {"en": "Date invoiced", "de": "Datum verrechnet"},
            "invoice":  {"en": "Invoice amount", "de": "Rechnungsbetrag"},
            "comment": {"en": "Comment", "de": "Kommentar"},

            "documents.order": {"en": "OR:", "de": "BE:"},
            "documents.orderconfirmation": {"en": "OC:", "de": "AB:"},
            "documents.delivery": {"en": "DE:", "de": "LS:"},
            "documents.invoice": {"en": "IN:", "de": "RE:"},
            "documents.undefined": {"en": "UN:", "de": "AN:"},

            "_predefined_filters.projects-running": {"en": "running projects", "de": "laufende Projekte"},
            "_predefined_filters.projects-finished": {"en": "finished projects only", "de": "nur abgeschlossene Projekte"},
            "_predefined_filters.projects-all": {"en": "all projects", "de": "alle Projekte"},
            "_predefined_filters.orderings-last-3-years": {"en": "last 3 years", "de": "letzte 3 Jahre"}
        }
    }


HTTP request using the ``predef_filter`` option:

.. code-block:: shell

   http://localhost:8080/ordermanagement-api/orderings?version=1&language=de&predef_filter=default

This leads to the following SQL query:

.. code-block:: sql

   SELECT orderings.idordering,orderings.order_nameid,orderings.idsupplier,orderings.material,
          orderings.idproject,orderings.idemployee_ordered,orderings.order_state,
          orderings.date_ordered,orderings.date_invoice_planned,orderings.date_planned,
          orderings.date_delivered,orderings.date_invoiced_done,orderings.invoice,orderings.comment
   FROM orderings INNER JOIN projects
   ON orderings.idproject=projects.idproject AND projects.project_state='running'

The resulting JSON data looks like this:

.. code-block:: json
    :linenos:

    {
        "orderings": {
            "idordering": 1, "order_nameid": "1000", "idsupplier": 1, "material": "Kable AWG21", "idproject": 1,
            "idemployee_ordered": 2, "order_state": "delivered", "date_ordered": "2019-11-03",
            "date_invoice_planned": "2019-12-01", "date_planned": "2019-11-17", "date_delivered": "2019-11-08",
            "date_invoiced_done": "2019-11-04", "invoice": "553.00", "comment": ""
        },
        "DT_RowId": 1,
        "suppliers": {"idsupplier": 1, "name": "Testlieferant 1"},
        "projects": {"idproject": 1, "name": "Projekt Test 1", "comment": "", "project_state": "running",
                     "date_started": null, "date_finished": null},
        "employees": {"idemployee": 2, "abbr": "JT", "firstname": "John", "lastname": "Test", "credential_hash":
                     "$6$rounds=656000$ROl.xoVbJEyGuK71$1Zn0S4tZkTPmoQ1HwayC0QUbZvJDbTXpjecmCCtWnmeqDSZh.Q76dr/ZRgLVPw9aTgl3eEnIkT7tlFBITccSO/",
                     "authentication_level": 0, "state": "active"},
        "orderings_order_state": {"name": "geliefert"}
    }

.. todo:: never transfer credentials because only token the identification is used!
