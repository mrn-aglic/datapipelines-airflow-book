from pathlib import Path

from airflow import DAG, settings
from airflow.models import Connection
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.s3_delete_objects import (
    S3DeleteObjectsOperator,
)
from airflow.utils import dates

dag = DAG(
    dag_id="RUN_FIRST_setup_env",
    schedule_interval=None,
    start_date=dates.days_ago(1),
)


def _check_aws_conn_exists():
    connections = settings.Session.query(Connection)
    connection_ids = [conn.conn_id for conn in connections]
    conn_exists = "aws_conn" in connection_ids

    if conn_exists:
        print("connection already exists, skipping upstream task")

    return not conn_exists


def _upload_resource():
    filename = "mnist.pkl.gz"
    file_path = f"/dataset/{filename}"
    mnist_file = Path(file_path)

    if mnist_file.exists():
        print("File /dataset/mnist.pkl.gz exists")

        hook = S3Hook(aws_conn_id="locals3")
        print("Hook connected")

        hook.load_file(
            filename=file_path,
            key=f"algorithms/kmeans/mnist/{filename}",
            bucket_name="sagemaker-sample-data-eu-west-1",
        )

        print("File successfully added to minio")
    else:
        raise Exception(f"File not found: {file_path}")


# Can be removed after minio mc cp command starts working. Currently gives:
# Unable to validate source `dataset/mnist.pkl.gz`.
# Run this DAG first manually to setup env
upload_resource = PythonOperator(
    task_id="upload_resource",
    python_callable=_upload_resource,
    dag=dag,
)

delete_resource = S3DeleteObjectsOperator(
    task_id="delete_resource",
    bucket="sagemaker-sample-data-eu-west-1",
    keys="algorithms/kmeans/mnist/mnist.pkl.gz",
    aws_conn_id="locals3",
    dag=dag,
)

short_circuit_aws_conn = ShortCircuitOperator(
    task_id="conditional_continue_aws_conn",
    python_callable=_check_aws_conn_exists,
    # dag=dag,
)

# Add the aws_conn to the UI. For some reason, the aws_conn doesn't work if
# it is not added through the UI
add_aws_conn = BashOperator(
    task_id="add_aws_conn",
    bash_command="airflow connections add aws_conn --conn-uri $AIRFLOW_CONN_AWS_CONN",
    # dag=dag,
)

short_circuit_aws_conn >> add_aws_conn

delete_resource >> upload_resource
