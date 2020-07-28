#!/bin/bash

echo
# go into the directory where the script is stored
cd "$(dirname "${0}")"
echo "Running script in $(pwd)"
echo

# start the conversion from MySQL syntax to SQLite syntax
/usr/bin/env python3 ../../flask_squirrel/tools/mysql_to_sqlite_convert.py test-db-model_mysql.sql test-db-model_sqlite.sql
echo "Finished."
echo
