import os
from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

with DAG(
    dag_id="02_docker_load_to_postgres",
    description="Fetch ratings from the movielens API using Docker.",
    start_date=datetime(2019, 1, 1),
    end_date=datetime(2019, 1, 3),
    schedule_interval="@daily",
) as dag:
    fetch_ratings = DockerOperator(
        task_id="fetch_ratings",
        image="airflowbook/movielens-fetch",
        auto_remove=True,
        command=[
            "fetch-ratings",
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
        mount_tmp_dir=False,
        mounts=[Mount(source="/tmp/airflow/data", target="/data", type="bind")],
        network_mode="airflow",  # make sure that the container is attached to the airflow Docker network
        # so that it can reach the API running on the same network
    )

    rank_movies = DockerOperator(
        task_id="rank_movies",
        image="airflowbook/movielens-rank",
        auto_remove=True,
        command=[
            "rank-movies",
            "--input_path",
            "/data/ratings/{{ ds }}.json",
            "--output_path",
            "/data/rankings/{{ ds }}.json",
        ],
        mount_tmp_dir=False,
        mounts=[Mount(source="/tmp/airflow/data", target="/data", type="bind")],
    )

    store_to_postgres = DockerOperator(
        task_id="store_to_postgres",
        image="airflowbook/store-movielens",
        auto_remove=True,
        command=[
            "store-movies",
            "--input_path",
            "/data/rankings/{{ ds }}.json",
            "--user",
            os.environ["MOVIELENS_DB_USER"],
            "--password",
            os.environ["MOVIELENS_DB_PASSWORD"],
            "--host",
            os.environ["MOVIELENS_DB_HOST"],
            "--port",
            "5432",
            "--date",
            "{{ ds }}",
        ],
        mount_tmp_dir=False,
        network_mode="airflow",
        mounts=[Mount(source="/tmp/airflow/data", target="/data", type="bind")],
    )

    fetch_ratings >> rank_movies >> store_to_postgres
