from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.s3_copy_object import S3CopyObjectOperator
from airflow.utils import dates

dag = DAG(
    dag_id="01_s3_copy_object_fixed",
    start_date=dates.days_ago(3),
    schedule_interval="@daily",
)


def _create_file(ds, **context):
    print("Connecting...")
    s3_hook = S3Hook(aws_conn_id="locals3")
    s3_hook.load_string(
        string_data=ds,
        key=f"/data/{ds}.json",
        bucket_name="data",
    )
    print("String loaded")


create_file = PythonOperator(
    task_id="create_file_task",
    python_callable=_create_file,
    dag=dag,
)

s3_copy = S3CopyObjectOperator(
    task_id="copy_s3_object",
    source_bucket_name="data",
    source_bucket_key="/data/{{ ds }}.json",
    dest_bucket_name="data-backup",
    dest_bucket_key="/data-backup/{{ ds }}-backup.json",
    aws_conn_id="locals3",
    dag=dag,
)

create_file >> s3_copy
