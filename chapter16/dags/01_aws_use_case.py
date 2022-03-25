import datetime as dt
import logging
import os
import tempfile
from os import path

import pandas as pd
from airflow import DAG, AirflowException
from airflow.models import Variable
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.athena import AWSAthenaOperator
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator
from airflow.utils.trigger_rule import TriggerRule
from custom.hooks import MovielensHook
from custom.operators import GlueTriggerCrawlerOperator


def _fetch_ratings(api_conn_id, s3_conn_id, s3_bucket, **context):
    year = context["execution_date"].year
    month = context["execution_date"].month

    logging.info("Fetching ratings for %d-%02d", year, month)

    api_hook = MovielensHook(conn_id=api_conn_id)

    ratings = pd.DataFrame.from_records(
        api_hook.get_ratings_for_month(year=year, month=month),
        columns=["userId", "movieId", "rating", "timestamp"],
    )

    logging.info("Fetched %d rows.", ratings.shape[0])

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = path.join(tmp_dir, "ratings.csv")
        ratings.to_csv(tmp_path, index=False)

        logging.info("Writing results to ratings/%d/%02d.csv", year, month)

        s3_hook = S3Hook(s3_conn_id)

        # upload the written ratings to S3 using the S3 hook
        s3_hook.load_file(
            tmp_path,
            key=f"ratings/{year}/{month:02d}.csv",
            bucket_name=s3_bucket,
            replace=True,
        )


def _choose_crawler():
    next_task = Variable.get("USE_CRAWLER", Variable.get("PROVIDED_CRAWLER"))

    print(next_task)

    if next_task in ("glue_crawler", "trigger_crawler"):
        return next_task

    raise AirflowException(f"Task with name {next_task} not found in DAG")


with DAG(
    dag_id="01_aws_use_case",
    description="DAG demonstrating some AWS specific operators and hooks",
    start_date=dt.datetime(2019, 1, 1),
    end_date=dt.datetime(2019, 3, 1),
    schedule_interval="@monthly",
    default_args={"depends_on_past": True},
) as dag:
    fetch_ratings = PythonOperator(
        task_id="fetch_ratings",
        python_callable=_fetch_ratings,
        op_kwargs={
            "api_conn_id": "movielens",
            "s3_conn_id": "aws_conn",
            "s3_bucket": os.environ["RATINGS_BUCKET"],
        },
    )

    crawler_choice = BranchPythonOperator(
        task_id="crawler_choice", python_callable=_choose_crawler
    )

    trigger_crawler = GlueTriggerCrawlerOperator(
        task_id="trigger_crawler",
        aws_conn_id="aws_conn",
        crawler_name=os.environ["CRAWLER_NAME"],
    )

    glue_crawler = GlueCrawlerOperator(
        task_id="glue_crawler",
        config={"Name": os.environ["CRAWLER_NAME"]},
        aws_conn_id="aws_conn",
    )

    rank_movies = AWSAthenaOperator(
        task_id="rank_movies",
        aws_conn_id="aws_conn",
        database="airflow",
        query="""
        SELECT movieId, AVG(rating) as avg_rating, COUNT(*) as num_ratings
        FROM (
            SELECT movieid, rating, CAST(from_unixtime(timestamp) AS DATE) AS date
            FROM ratings
        )
        WHERE date <= DATE('{{ ds }}')
        GROUP BY movieId
        ORDER BY avg_rating DESC
        """,
        output_location=f"s3://{os.environ['RANKINGS_BUCKET']}/{{{{ds}}}}",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    fetch_ratings >> crawler_choice >> [trigger_crawler, glue_crawler] >> rank_movies
