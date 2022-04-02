# Chapter 18 - GCP

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

## Additional GCP setup details for DAG
### Fetch ratings
You need to manually create a bucket and assign another role to
the user. You can pick one of these two (I suggest the first one):
- Storage Object Admin - if you want to be able to re-run the
DAG.
- Storage Object Creator - if you plan to run the DAG once for
each execution date.

The chapter skips on creating the bucket and assigning this role.

### GCS to BigQuery (import in bigquery)
You should manually create a dataset and also assign the appropriate
role to the service account. In my case, I assigned the user the
role:
- BigQuery Data Editor

### Big query to GCS
Make sure to create a gcs bucket for storing the results from
BQ.
