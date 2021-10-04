import gzip
import io
import pickle

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.s3_copy_object import S3CopyObjectOperator
from airflow.providers.amazon.aws.operators.sagemaker_endpoint import (
    SageMakerEndpointOperator,
)
from airflow.providers.amazon.aws.operators.sagemaker_training import (
    SageMakerTrainingOperator,
)
from airflow.utils import dates
from sagemaker.amazon.common import write_numpy_to_dense_tensor

S3_CONNECTION_ID = "aws_conn"

mnist_filename = "mnist.pkl.gz"
my_bucket = "marin-airflow-book-data"
sagemaker_output_path = f"s3://{my_bucket}/mnistclassifier-output"

TRAINING_IMAGE = "438346466558.dkr.ecr.eu-west-1.amazonaws.com/kmeans:latest"
ROLE_ARN = "arn:aws:iam::221767510175:role/airflow-book-sagemaker"  # needs to be configured on aws

SAGEMAKER_DEPLOY_OPERATION = (
    "update"  # create or update - for first time models, needs to be create
)

SAGEMAKER_CONFIG = {
    "algorithm_specification": {
        # "training_image": "438346466558.dkr.ecr.eu-west-1.amazonaws.com/kmeans:1", # from the book
        "TrainingImage": TRAINING_IMAGE,
        "TrainingInputMode": "File",
    },
    "hyper_parameters": {"k": "10", "feature_dim": "784"},
    "input_data_config": [
        {
            "ChannelName": "train",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"s3://{my_bucket}/mnist_data",
                    "S3DataDistributionType": "FullyReplicated",
                }
            },
        }
    ],
    "role_arn": ROLE_ARN,
}

dag = DAG(
    dag_id="aws_handwritten_digit_classifier",
    schedule_interval=None,
    start_date=dates.days_ago(3),
)

sagemaker_train_model = SageMakerTrainingOperator(
    task_id="sagemaker_train_model",
    config={
        "TrainingJobName": "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}",
        "AlgorithmSpecification": SAGEMAKER_CONFIG["algorithm_specification"],
        "HyperParameters": SAGEMAKER_CONFIG["hyper_parameters"],
        "InputDataConfig": SAGEMAKER_CONFIG["input_data_config"],
        "OutputDataConfig": {"S3OutputPath": sagemaker_output_path},
        "ResourceConfig": {
            "InstanceType": "ml.c4.xlarge",
            "InstanceCount": 1,
            "VolumeSizeInGB": 10,
        },
        "RoleArn": SAGEMAKER_CONFIG["role_arn"],
        # "RoleArn": "arn:aws:iam::297623009465:role/service-role/AmazonSageMaker-ExecutionRole-20180905T153196",
        "StoppingCondition": {"MaxRuntimeInSeconds": 24 * 60 * 60},
    },
    wait_for_completion=True,
    print_log=True,
    check_interval=10,
    aws_conn_id=S3_CONNECTION_ID,
    dag=dag,
)

SAGEMAKER_DEPLOY_CONFIG = {
    "Model": {
        # "ModelName": "mnistclassifier",
        "ModelName": "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}",
        "PrimaryContainer": {
            "Image": TRAINING_IMAGE,
            "ModelDataUrl": (
                f"{sagemaker_output_path}/"
                "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}/"
                "output/model.tar.gz"
            ),  # this will link the model and the training job
        },
        "ExecutionRoleArn": ROLE_ARN,
    },
    "EndpointConfig": {
        "EndpointConfigName": "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}",
        "ProductionVariants": [
            {
                "InitialInstanceCount": 1,
                "InstanceType": "ml.t2.medium",
                "ModelName": "mnistclassifier",
                # "ModelName": "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}",  #
                "VariantName": "AllTraffic",
            }
        ],
    },
    "Endpoint": {
        "EndpointConfigName": "mnistclassifier-{{ execution_date.strftime('%Y-%m-%d-%H-%M-%S') }}",
        "EndpointName": "mnistclassifier",
    },
}

sagemaker_deploy_model = SageMakerEndpointOperator(
    task_id="sagemaker_deploy_model",
    wait_for_completion=True,
    config=SAGEMAKER_DEPLOY_CONFIG,
    operation=SAGEMAKER_DEPLOY_OPERATION,
    aws_conn_id=S3_CONNECTION_ID,
    dag=dag,
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


def _extract_mnist_data():
    s3_hook = S3Hook(S3_CONNECTION_ID)

    # Download data into memory
    mnist_buffer = io.BytesIO()
    mnist_obj = s3_hook.get_key(bucket_name=my_bucket, key=mnist_filename)
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
            output_buffer, key="mnist_data", bucket_name=my_bucket, replace=True
        )


extract_mnist_data = PythonOperator(
    task_id="extract_mnist_data",
    python_callable=_extract_mnist_data,
    dag=dag,
)

copy_mnist_data >> extract_mnist_data >> sagemaker_train_model >> sagemaker_deploy_model
