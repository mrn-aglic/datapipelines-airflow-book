import gzip
import io
import pickle

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.s3_copy_object import S3CopyObjectOperator
from airflow.utils import dates
from sagemaker.amazon.common import write_numpy_to_dense_tensor

mnist_filename = "mnist.pkl.gz"

dag = DAG(
    dag_id="minio_handwritten_digit_classifier",
    schedule_interval=None,
    start_date=dates.days_ago(3),
)


def _extract_mnist_data():
    s3_hook = S3Hook("locals3")

    # Download data into memory
    mnist_buffer = io.BytesIO()
    mnist_obj = s3_hook.get_key(bucket_name="data", key=mnist_filename)
    mnist_obj.download_fileobj(mnist_buffer)

    # Unpack gzip file, extract dataset, convert, upload back to S3
    mnist_buffer.seek(0)
    with gzip.GzipFile(fileobj=mnist_buffer, mode="rb") as f:
        train_set, _, _ = pickle.loads(f.read(), encoding="latin1")
        output_buffer = io.BytesIO()
        write_numpy_to_dense_tensor(
            file=output_buffer,
            array=train_set[0],
            labels=train_set[1],
        )
        output_buffer.seek(0)
        s3_hook.load_file_obj(
            output_buffer, key="mnist_data", bucket_name="data", replace=True
        )


copy_mnist_data = S3CopyObjectOperator(
    task_id="copy_mnist_data",
    source_bucket_name="sagemaker-sample-data-eu-west-1",
    source_bucket_key="algorithms/kmeans/mnist/mnist.pkl.gz",
    dest_bucket_name="data",  # my account bucket
    dest_bucket_key=mnist_filename,
    aws_conn_id="locals3",
    dag=dag,
)

extract_mnist_data = PythonOperator(
    task_id="extract_mnist_data",
    python_callable=_extract_mnist_data,
    dag=dag,
)

copy_mnist_data >> extract_mnist_data
