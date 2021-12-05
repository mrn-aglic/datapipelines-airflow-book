# Chapter 08

## Note on `python_scripts` directory

_If you like you can completely ignore this directory
as the functions implemented in it are also used in
the `01_fetch_ratings_python` DAG._

The python_scripts directory contains the
`fetching_ratings_api.py` script that queries the
movielens api endpoint. To run the script, first build the
docker image via:
```
docker build -t python_scripts python_scripts
```
If running from the chapter08 directory.

Run the docker container:
```
docker run --network="host" python_scripts
```
Make sure that the movielens-api is running.

## Airflowbook package
airflow_book_package is added as a git submodule.
Refer to the Readme of the git repo for additional
details:
https://github.com/mrn-aglic/airflow_book_example_package_repo
