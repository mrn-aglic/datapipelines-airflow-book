from airflow import DAG
from airflow.providers.amazon.aws.operators.s3_copy_object import S3CopyObjectOperator
from airflow.utils import dates

S3_CONNECTION_ID = "aws_conn"

mnist_filename = "mnist.pkl.gz"
my_bucket = "marin-airflow-book-data"

dag = DAG(
    dag_id="test_dag",
    schedule_interval=None,
    start_date=dates.days_ago(3),
)

copy_mnist_data = S3CopyObjectOperator(
    task_id="copy_mnist_data",
    source_bucket_name="sagemaker-sample-data-eu-west-1",
    source_bucket_key="algorithms/kmeans/mnist/mnist.pkl.gz",
    dest_bucket_name=f"{my_bucket}",  # my account bucket
    dest_bucket_key=mnist_filename,
    aws_conn_id=S3_CONNECTION_ID,
    dag=dag,
)
