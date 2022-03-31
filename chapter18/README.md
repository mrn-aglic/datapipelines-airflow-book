# Chapter 18 - GCP

Most of this Readme is taken directly from the book [GitHub repo](https://github.com/BasPH/data-pipelines-with-apache-airflow).

Note that for setting up gke cluster, I had to run the command:
```shell
gcloud services enable container.googleapis.com
```
before running the command:
```shell
gcloud container clusters create my-airflow-cluster \
--machine-type n1-standard-4 \
--num-nodes 1 \
--region "europe-west4"
```
Next run
```shell
gcloud container clusters get-credentials my-airflow-cluster \
--region europe-west4
```
as described in the chapter.

To deploy airflow, I did not follow the commands in listing 13.3.\
I did the following:
1. install helm:
    ```shell
   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
   chmod 700 get_helm.sh
   ./get_helm.sh
   ```
2. add apache-airflow repository and install
    ```shell
    helm repo add apache-airflow https://airflow.apache.org
    helm upgrade --install airflow apache-airflow/airflow --namespace airflow --debug
    ```
3. the webserver runs as a Kubernetes ClusterIP service, which gives
gives you a service that other applications can access. However,
it isn't  externally accessible. To access it we can port forward
to the port
    ```shell
    kubectl port-forward svc/airflow-webserver 8080:8080 --namespace airflow
    ```

Change the webserver from ClusterIP to LoadBalancer service:
1. run
```shell
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --set webserver.service.type=LoadBalancer --debug
```

For installing and enabling KEDA I used the following commands
to prepare everything:

```shell
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
kubectl create namespace keda
helm install keda kedacore/keda \
--namespace keda \
--version "v2.0.0"
```

Now, running the following command disabled the load balancer that
was previously configured:
```shell
helm upgrade airflow apache-airflow/airflow --namespace airflow --set workers.keda.enabled=True --debug
```

I assume it that all the values we want to change need to
be provided at the time that the helm upgrade command is executed.
For a better understanding of what is going on, please take a look
at [this link](https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e).

Anyway, I created the file `resources/helm-override.yaml` that
contains all overrides.

You should navigate to the folder chapter18 and execute the command:
```shell
helm upgrade -f resources/helm-override.yaml airflow apache-airflow/airflow --namespace airflow --debug
```



The details I followed for deployment [can be found here](https://towardsdatascience.com/deploying-airflow-on-google-kubernetes-engine-with-helm-28c3d9f7a26b).
Note that in my case helm configured the deployment with the
CeleryExecutor instead of the KubernetesExecutor
as mentioned in the book.

Code accompanying the GCP section of Chapter 18 in the book 'Data pipelines with Apache Airflow'.

## Contents

This code example contains the following files:

├── Makefile            # Makefile for helping run commands.
├── dags
│   └── gcp.py          # The actual DAG.
├── docker-compose.yml  # Docker-compose file for Airflow.
├── README.md           # This file.
└── scripts
    └── fetch_data.py   # Helper script for fetching data.

## Usage

To get started with the code example, first make sure to fetch the required dataset:

    make data/ratings

Next, use the GCP console (or other tool of choice) to create the following resources for the DAG:

* GCS bucket

How to create these resources (+ what settings to used) is described in the Chapter.

Once the required resources have been created, you can start Airflow to run the DAG:

    make airflow-start

You can tear down the Airflow resources using

    make airflow-stop
