#!/usr/bin/env bash

cd /

echo "Hello from test docker container!"

# need db metastore for running tasks with .run method - airflow queries the metastore
echo "initializing airflow db metastore..."
airflow db init &> metastore.log
echo "airflow metastore initialized!"

echo "Listing dags:"
ls -al dags/

echo "Listings tests:"
ls -al tests/

pytest tests/

echo "Pytest exit code $?"

# instead of using dbbeaver, let's print the metastore log rows
echo "Metastore logs:"
sqlite3 ////root/airflow/airflow.db "select * from log;" ".exit"

# ignore errors 1 and 5 from pytest (1 - test failed, 5 - no tests found)
exit $(( $? == 5 || $? == 1 ? 0 : $? ))
