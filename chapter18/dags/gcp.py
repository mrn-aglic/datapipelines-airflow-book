import logging
import os
import tempfile
from datetime import datetime
from os import path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryDeleteTableOperator,
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import (
    BigQueryToGCSOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from custom.hooks import MovielensHook


def _fetch_ratings(api_conn_id, gcp_conn_id, gcs_bucket, **context):
    year = context["execution_date"].year
    month = context["execution_date"].month

    logging.info("Fetching ratings for %d/%02d", year, month)

    api_hook = MovielensHook(conn_id=api_conn_id)

    ratings = pd.DataFrame.from_records(
        api_hook.get_ratings_for_month(year=year, month=month),
        columns=["userId", "movieId", "rating", "timestamp"],
    )

    logging.info("Fetched %d rows", ratings.shape[0])

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = path.join(tmp_dir, "ratings.csv")
        ratings.to_csv(tmp_path, index=False)

        # upload file to GCS
        logging.info("Writing results to ratings/%s/%02d.csv", year, month)
        gcs_hook = GCSHook(gcp_conn_id=gcp_conn_id)

        object_name = f"ratings/{year}/{month:02d}.csv"
        # gcs_hook.delete(bucket_name=gcs_bucket, object_name=object_name)
        gcs_hook.upload(
            bucket_name=gcs_bucket,
            object_name=object_name,
            filename=tmp_path,
        )


with DAG(
    dag_id="gcp_movie_ranking",
    description="DAG demonstrating some GCP hooks and operators.",
    start_date=datetime(year=2019, month=1, day=1),
    end_date=datetime(year=2019, month=3, day=1),
    schedule_interval="@monthly",
    default_args={"depends_on_past": True},
) as dag:
    fetch_ratings = PythonOperator(
        task_id="fetch_ratings",
        python_callable=_fetch_ratings,
        op_kwargs={
            "api_conn_id": "movielens",
            "gcp_conn_id": "google_cloud",
            "gcs_bucket": os.environ["RATINGS_BUCKET"],
        },
    )

    import_in_bigquery = GCSToBigQueryOperator(
        task_id="import_in_bigquery",
        bucket=os.environ["RATINGS_BUCKET"],
        source_objects=[
            "ratings/{{ execution_date.year }}/{{ execution_date.strftime('%m') }}.csv"
        ],
        source_format="CSV",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
        bigquery_conn_id="google_cloud",
        skip_leading_rows=1,
        schema_fields=[
            {"name": "userId", "type": "INTEGER"},
            {"name": "movieId", "type": "INTEGER"},
            {"name": "rating", "type": "FLOAT"},
            {"name": "timestamp", "type": "TIMESTAMP"},
        ],
        destination_project_dataset_table=os.environ["GCP_PROJECT"]
        + "."
        + os.environ["BIGQUERY_DATASET"]
        + ".ratings${{ ds_nodash }}",
    )

    # at the time of reading the chapter and writing this code, BigQueryExecuteQueryOperator is deprecated
    # so I'm using the BigQueryInsertJobOperator in its place
    query_top_ratings = BigQueryInsertJobOperator(
        task_id="query_top_ratings",
        configuration={
            "query": {
                "query": f"""CREATE OR REPLACE TABLE `{os.environ["BIGQUERY_DATASET"]}.temp_topratings_{{{{ ds_nodash }}}}` AS
                SELECT movieId, AVG(rating) as avg_rating, COUNT(*) as num_ratings
                FROM `{os.environ["BIGQUERY_DATASET"]}.ratings`
                WHERE DATE(timestamp) <= DATE("{{{{ ds }}}}")
                GROUP BY movieId
                ORDER BY avg_rating DESC
                """,
                "useLegacySql": False,
            }
        },
        gcp_conn_id="google_cloud",
    )

    extract_top_ratings = BigQueryToGCSOperator(
        task_id="extract_top_ratings",
        gcp_conn_id="google_cloud",
        source_project_dataset_table=f"{os.environ['BIGQUERY_DATASET']}.temp_topratings_{{{{ ds_nodash }}}}",
        destination_cloud_storage_uris=[
            f"gs://{os.environ['RESULT_BUCKET']}/{{{{ ds_nodash }}}}.csv"
        ],
        export_format="CSV",
    )

    delete_temp_table = BigQueryDeleteTableOperator(
        task_id="delete_temp_table",
        deletion_dataset_table=f"{os.environ['GCP_PROJECT']}.{os.environ['BIGQUERY_DATASET']}.temp_topratings_{{{{ ds_nodash }}}}",
        gcp_conn_id="google_cloud",
    )

    (
        fetch_ratings
        >> import_in_bigquery
        >> query_top_ratings
        >> extract_top_ratings
        >> delete_temp_table
    )
