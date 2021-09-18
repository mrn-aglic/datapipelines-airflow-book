from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.s3_copy_object import S3CopyObjectOperator
from airflow.providers.amazon.aws.operators.s3_list import S3ListOperator
from airflow.providers.amazon.aws.sensors.s3_key import S3KeySensor
from airflow.utils import dates

dag = DAG(
    dag_id="aws_handwritten_digit_classifier",
    schedule_interval=None,
    start_date=dates.days_ago(3),
)


def _print_keys(keys):
    print(keys)


def _download_from_aws_to_minio():
    src_hook = S3Hook(aws_conn_id="aws_conn")
    filename = src_hook.download_file(
        "sagemaker-sample-data-eu-west-1", key="algorithms/kmeans/mnist/mnist.pkl.gz"
    )

    dst_hook = S3Hook(aws_conn_id="locals3")
    dst_hook.load_file(filename=filename, bucket_name="data", key="data")


list_keys = S3ListOperator(
    task_id="list_keys",
    bucket="sagemaker-sample-data-eu-west-1",  # public aws bucket from book author
    prefix="algorithms/",
    # delimiter="/",
    aws_conn_id="aws_conn",  # create an access key on aws
    dag=dag,
)

print_keys = PythonOperator(
    task_id="print_keys",
    python_callable=_print_keys,
    op_kwargs={"keys": "{{ti.xcom_pull(task_ids='list_keys', key='return_value')}}"},
    dag=dag,
)

# download_mnist_data_from_aws_to_minio = PythonOperator(
#     task_id="download_from_aws_to_minio",
#     python_callable=_download_from_aws_to_minio,
#     dag=dag,
# )

download_mnist_data = S3CopyObjectOperator(
    task_id="download_mnist_data",
    source_bucket_name="sagemaker-sample-data-eu-west-1",
    source_bucket_key="algorithms/kmeans/mnist/mnist.pkl.gz",
    dest_bucket_name="marin-data",  # my account bucket
    dest_bucket_key="data/mnist.pkl.gz",
    aws_conn_id="aws_conn",
    dag=dag,
)

list_keys >> print_keys
