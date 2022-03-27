import datetime as dt
import logging
import tempfile
from os import path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from airflow.providers.odbc.hooks.odbc import OdbcHook
from custom.hooks import MovielensHook

# OPENROWSET tells Synapse to load the data from our storage account
RANK_QUERY = """
SELECT movieId, AVG(rating) as avg_rating, COUNT(*) as num_ratings
FROM OPENROWSET(
    BULK 'https://{blob_account_name}.blob.core.windows.net/{blob_container}/*/*.csv',
    FORMAT='CSV',
    PARSER_VERSION='2.0',
    HEADER_ROW=TRUE,
    FIELDTERMINATOR=',',
    ROWTERMINATOR='\n'
)
WITH (
    [userId] bigint,
    [movieId] bigint,
    [rating] float,
    [timestmap] bigint
) as [r]
WHERE (
    (r.filepath(1) < '{year}') OR
    (r.filepath(1) = '{year}' AND r.filepath(2) <= '{month:02d}')
)
GROUP by movieId
ORDER BY avg_rating DESC;
"""


def _fetch_ratings(api_conn_id, wasb_conn_id, container, **context):
    year = context["execution_date"].year
    month = context["execution_date"].month

    logging.info("Fetching ratings for %d/%02d", year, month)

    api_hook = MovielensHook(api_conn_id)

    ratings = pd.DataFrame.from_records(
        api_hook.get_ratings_for_month(year=year, month=month),
        columns=["userId", "movieId", "rating", "timestmap"],
    )

    logging.info("Fetched %d rows", ratings.shape[0])

    # write ratings to temp file.
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = path.join(tmp_dir, "ratings.csv")
        ratings.to_csv(tmp_path, index=False)

        logging.info("Writing results to %s/%d/%02d", container, year, month)

        blob_name = f"{year}/{month:02d}.csv"

        hook = WasbHook(wasb_conn_id)

        hook.delete_file(
            blob_name=blob_name, container_name=container, ignore_if_missing=True
        )  # makes the operator idempotent
        hook.load_file(tmp_path, container_name=container, blob_name=blob_name)


def _rank_movies(
    odbc_conn_id, wasb_conn_id, ratings_container, rankings_container, **context
):
    year = context["execution_date"].year
    month = context["execution_date"].month

    blob_account_name = WasbHook.get_connection(
        wasb_conn_id
    ).login  # retrieve the name of our blob storage account (same as the login name
    # for the storage account)

    query = RANK_QUERY.format(
        year=year,
        month=month,
        blob_account_name=blob_account_name,
        blob_container=ratings_container,
    )

    logging.info("Executing query %s", query)

    odbc_hook = OdbcHook(odbc_conn_id, driver="ODBC Driver 18 for SQL Server")

    with odbc_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()
            colnames = [field[0] for field in cursor.description]

    ranking = pd.DataFrame.from_records(rows, columns=colnames)
    logging.info("Retrieved %d rows", ranking.shape[0])

    logging.info("Writing results to %s/%d/%02d", rankings_container, year, month)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = path.join(tmp_dir, "ranking.csv")
        ranking.to_csv(tmp_path, index=False)

        blob_name = f"{year}/{month:02d}.csv"

        # Upload file to Azure Blob.
        hook = WasbHook(wasb_conn_id)

        hook.delete_file(
            blob_name=blob_name,
            container_name=rankings_container,
            ignore_if_missing=True,
        )  # makes the operator idempotent

        hook.load_file(
            tmp_path,
            container_name=rankings_container,
            blob_name=blob_name,
        )


with DAG(
    dag_id="01_azure_usecase",
    description="DAG demonstrating some Azure hooks and operators.",
    start_date=dt.datetime(year=2019, month=1, day=1),
    end_date=dt.datetime(year=2019, month=3, day=1),
    schedule_interval="@monthly",
    default_args={"depends_on_past": True},
) as dag:
    fetch_ratings = PythonOperator(
        task_id="fetch_ratings",
        python_callable=_fetch_ratings,
        op_kwargs={
            "api_conn_id": "movielens",
            "wasb_conn_id": "wasb_conn",
            "container": "ratings",
        },
    )

    rank_movies = PythonOperator(
        task_id="rank_movies",
        python_callable=_rank_movies,
        op_kwargs={
            "odbc_conn_id": "odbc_conn",
            "wasb_conn_id": "wasb_conn",
            "ratings_container": "ratings",
            "rankings_container": "rankings",
        },
    )

    fetch_ratings >> rank_movies
