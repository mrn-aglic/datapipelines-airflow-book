import os
from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from kubernetes.client import models as k8s

with DAG(
    dag_id="01_kubernetes",
    description="Fetch ratings from the movielens API using Docker.",
    start_date=datetime(2019, 1, 1),
    end_date=datetime(2019, 1, 3),
    schedule_interval="@daily",
) as dag:
    volume_claim = k8s.V1PersistentVolumeClaimVolumeSource(
        claim_name="data-volume"  # the volume claim created with kubectl
    )
    volume = k8s.V1Volume(
        name="data-volume",  # volume created with kubectl
        persistent_volume_claim=volume_claim,
    )
    volume_mount = k8s.V1VolumeMount(
        name="data-volume",
        mount_path="/data",  # where to mount the volume in the pods container
        sub_path=None,
        read_only=False,  # mount the volume as writeable
    )

    fetch_ratings = KubernetesPodOperator(
        task_id="fetch_ratings",
        image="airflowbook/movielens-fetch:k8s",
        cmds=["fetch-ratings"],  # the executable to run inside the container
        arguments=[
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
        namespace="airflowbook",  # the kubernetes namespace to run the pod in
        name="fetch-ratings",  # name to use for the pod
        cluster_context="docker-desktop",
        in_cluster=False,  # we are not running airflow iteself inside the cluster
        volumes=[volume],
        volume_mounts=[volume_mount],
        image_pull_policy="Never",  # use locally built image
        is_delete_operator_pod=True,  # delete pods after they finish running
    )

    rank_movies = KubernetesPodOperator(
        task_id="rank_movies",
        image="airflowbook/movielens-rank:k8s",
        cmds=["rank-movies"],
        arguments=[
            "--input_path",
            "/data/ratings/{{ ds }}.json",
            "--output_path",
            "/data/rankings/{{ ds }}.json",
        ],
        namespace="airflowbook",
        name="fetch-ratings",
        cluster_context="docker-desktop",
        in_cluster=False,
        volumes=[volume],
        volume_mounts=[volume_mount],
        image_pull_policy="Never",
        is_delete_operator_pod=True,
    )

    fetch_ratings >> rank_movies
