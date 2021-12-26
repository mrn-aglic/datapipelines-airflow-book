import os
from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="01_docker",
    description="Fetch ratings from the movielens API using Docker.",
    start_date=datetime(2019, 1, 1),
    end_date=datetime(2019, 1, 3),
    schedule_interval="@daily",
) as dag:
    fetch_ratings = DockerOperator(
        task_id="fetch_ratings",
        image="airflowbook/movielens-fetch",
        command=[
            "fetch_ratings",
            "--start_date",
            "{{ ds }}",
            "--end_date",
            "{{ next_ds }}",
            "--output_path",
            "/data/ratings/{{ ds }}.json",
            "--user",
            os.environ["MOVIELENS_USER"],
            "--password",
            os.environ["MOVIELENS_PASSWORD"],
            "--host",
            os.environ["MOVIELENS_HOST"],
        ],
        volumes=["/tmp/airflow/data:/data"],
        network_mode="airflow",  # make sure that the container is attached to the airflow Docker network
        # so that it can reach the API running on the same network
    )

    rank_movies = DockerOperator(
        task_id="rank_movies",
        image="airflowbook/movielens-rank",
        command=[
            "rank-movies",
            "--input_path",
            "/data/ratings/{{ ds }}.json",
            "--output_path",
            "/data/rankings/{{ ds }}.json",
        ],
        volumes=["/tmp/airflow/data:/data"],
    )

    fetch_ratings >> rank_movies
