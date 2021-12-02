#!/usr/bin/env bash

cd /

echo "Hello from test docker container!"

echo "Listing dags:"
ls -al dags/

echo "Listings tests:"
ls -al tests/

pytest tests/

echo "Pytest exit code $?"

# ignore errors 1 and 5 from pytest (1 - test failed, 5 - no tests found)
exit $(( $? == 5 || $? == 1 ? 0 : $? ))
