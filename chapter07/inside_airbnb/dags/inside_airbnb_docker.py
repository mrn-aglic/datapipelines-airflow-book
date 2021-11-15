import os
from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from operators.postgres_to_s3 import PostgresToS3Operator

S3_BUCKET = "inside-airbnb"

dag = DAG(
    dag_id="inside_airbnb_docker",
    start_date=datetime(2020, 10, 1),
    end_date=datetime(2023, 12, 21),
    schedule_interval="@monthly",
    max_active_runs=1,
)

download_from_postgres = PostgresToS3Operator(
    task_id="download_from_postgres",
    postgres_conn_id="inside_airbnb",
    query="SELECT * FROM listings WHERE download_date BETWEEN '{{ prev_ds }}' AND '{{ ds }}'",
    # query="SELECT * FROM listings WHERE download_date = {{ ds }}",
    s3_conn_id="locals3",
    s3_bucket=S3_BUCKET,
    s3_key="listing_{{ ds }}.csv",
    dag=dag,
)

access_key = os.environ.get("S3_ACCESS_KEY")
secret_key = os.environ.get("S3_SECRET_KEY")

docker_host = os.environ.get("DOCKER_HOST")

crunch_numbers = DockerOperator(
    task_id="crunch_numbers",
    image="airflow_book/numbercruncher",
    api_version="auto",
    auto_remove=True,
    # docker_url="unix://var/run/docker.sock",
    docker_url=docker_host,
    network_mode="host",
    environment={
        "S3_ENDPOINT": "localhost:9000",
        "S3_ACCESS_KEY": access_key,
        "S3_SECRET_KEY": secret_key,
    },
    dag=dag,
)

download_from_postgres >> crunch_numbers
