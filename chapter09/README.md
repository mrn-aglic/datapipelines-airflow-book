# Chapter 09

I've created a simple docker image for running the tests.

To build the image run: `make build-tests`.<br>
Running the image: `make run-tests`. <br>
Build and run the image in a single command:
`make start-tests`.

Check out Makefile to see how the commands are
defined.

Note that for some tests, you'll need to have the code
from chapter08 up and running. You may also need to
input the name of the network that the services
use in the Makefile `run-tests` command.

Here is a list of the tests that won't work without the
code from chapter08 up and running:
- test_movielens_operators (tests/dags/chapter08/airflow_movielens)
-
