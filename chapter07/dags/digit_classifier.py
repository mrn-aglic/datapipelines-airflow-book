import gzip
import io
import pickle

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.s3_copy_object import S3CopyObjectOperator
from airflow.providers.amazon.aws.operators.sagemaker_training import (
    SageMakerTrainingOperator,
)
from airflow.utils import dates
from sagemaker.amazon.common import write_numpy_to_dense_tensor

SAGEMAKER = {
    # "training_image": "438346466558.dkr.ecr.eu-west-1.amazonaws.com/kmeans:1",
    "training_image": "438346466558.dkr.ecr.eu-west-1.amazonaws.com/kmeans:latest",
    # "training_image": "404615174143.dkr.ecr.us-east-2.amazonaws.com/knn",
    # "training_image": "763104351884.dkr.ecr.eu-west-3.amazonaws.com",
    "hyper_parameters": {"k": 10, "feature_dim": 784},
}

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


sagemaker_train_model = SageMakerTrainingOperator(
    task_id="sagemaker_train_model",
    config={
        "TrainingJobName": "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}",
        "AlgorithmSpecification": {
            "TrainingImage": SAGEMAKER["training_image"],
            "TrainingInputMode": "File",
        },
        "HyperParameters": SAGEMAKER["hyper_parameters"],
        "InputDataConfig": [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": "s3://data/mnist_data",
                        "S3DataDistributionType": "FullyReplicated",
                    }
                },
            }
        ],
        "OutputDataConfig": {"S3OutputPath": "s3://data/mnistclassifier-output"},
        "ResourceConfig": {
            "InstanceType": "ml.c4.xlarge",
            "InstanceCount": 1,
            "VolumeSizeInGB": 10,
        },
        "RoleArn": "arn:aws:iam::297623009465:role/service-role/AmazonSageMaker-ExecutionRole-20180905T153196",
        "StoppingCondition": {"MaxRuntimeInSeconds": 24 * 60 * 60},
    },
    wait_for_completion=True,
    print_log=True,
    check_interval=10,
    aws_conn_id="locals3",
    dag=dag,
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

copy_mnist_data >> extract_mnist_data >> sagemaker_train_model
