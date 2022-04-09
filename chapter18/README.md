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

# Actually running airflow DAGs on GCP
The book does not actually provide insights on how to actually
run the dags on GCP. It explains how to deploy airflow
and how to use some GCP specific operators and hooks.

So, I'll try to explain what I did here.

**Note: I'm writing this from memory after a few days, so feel free
to notify me if I make a mistake or skip some step.
I'll also try to remember the references I used for setting
it up.**

## Creating a custom Docker image
We need to create a custom docker image that has the
`apache-airflow-providers-google` package installed and deploy
that image to the artifact registry on GCP.
1. enable the artifact registry API on GCP for your project.
This may take a few minutes to complete.
2. run the command:
   ```shell
   gcloud auth configure-docker europe-west4-docker.pkg.dev
   ```
3. create the docker repository:
   ```shell
   gcloud artifacts repositories create airflow-gke --repository-format=docker --location=europe-west4 --description="Docker repository for custom Airflow images"
   ```
4. navigate to `chapter18/airflow-gcp` and run the following
command:
   ```shell
   docker build -t europe-west4-docker.pkg.dev/<project-id>/airflow-gke/airflow-ch18:latest .
   ```
   Don't forget to replace `<project-id>` with the id of your
   GCP project.
5. run (and re-run) the command until all of the layers are
successfully published:
   ```shell
   docker push europe-west4-docker.pkg.dev/<project-id>/airflow-gke/airflow-ch18:latest
   ```
   Again, replace `<project-id>` with the id of your GCP project.
6. now we need to change the deployment so that kubernetess
uses our custom image when creating pods. The following part of
the `resources/helm-override.yaml` does this:
   ```shell
   images:
     airflow:
       repository: europe-west4-docker.pkg.dev/<project-id>/airflow-gke/airflow-ch18
       tag: latest
       pullPolicy: IfNotPresent
   ```
7. navigate to `chapter18` and redeploy:
```shell
helm upgrade --install airflow apache-airflow/airflow -n airflow -f resources/helm-override.yaml --debug
```

## Enabling git-sync and exposing environment variables
The first thing we need to do is have access to our DAGs.
I used git-sync for this. Run the following set of commands:
1. create a new ssh key with the email of your github account:
   ```shell
   ssh-keygen -t rsa -b 4096 -C "<john.doe@gmail.com>"
   ```
2. next copy the generated key:
   ```shell
   cat <path>/id_rsa.pub
   ```
3. paste the key on GitHub (I used GitHub) in the `settings >
deploy keys > Add Deploy key`. Note: you do not need to allow
write access.
4. In the resources/helm-override.yaml contains the section
that will enable the deployment to sync with git:
   ```yaml
   dags:
     gitSync:
       enabled: true
       repo: https://github.com/<your-repository>
       branch: master
       subPath: <sub-path>
       sshKeySecret: <kubectl-secret-name>
   ```
in this case (my repo), it looks like this:
```yaml
dags:
  gitSync:
    enabled: true
    repo: https://github.com/mrn-aglic/datapipelines-airflow-book.git
    branch: master
    subPath: "chapter18/dags"
    sshKeySecret: airflow-gke-git-secret
```
5. we need to create the kubectl secret. I named it
`airflow-gke-git-secret`. To create it, run the following
command:
   ```yaml
   kubectl create secret generic airflow-gke-git-secret --from-file=/Users/marinaglic/.ssh/id_rsa.pub --namespace airflow
   ```
6. redeploy:
   ```shell
   helm upgrade --install airflow apache-airflow/airflow -n airflow -f resources/helm-override.yaml --debug
   ```

If memory servers, when you deploy airflow to GCP now,
the dags fodler should be synced and you should be able
to see the DAG in the UI. However, it still won't run
successfully.

The second thing we need to do is have our environment variables
on GCP. I managed to do this with the following commands:
1. create a secret from the `.env` file that contains our
variables:
   ```shell
   kubectl create secret generic airflow-ch18-env --from-env-file .env -n airflow
   ```
2. our pods need to access the secrets that are defined. The
following part of `resources/helm-override.yaml` does this:
   ```yaml
   secret:
     - envName: RATINGS_BUCKET
       secretName: airflow-ch18-env
       secretKey: RATINGS_BUCKET
     - envName: RESULT_BUCKET
       secretName: airflow-ch18-env
       secretKey: RESULT_BUCKET
     - envName: BIGQUERY_DATASET
       secretName: airflow-ch18-env
       secretKey: BIGQUERY_DATASET
     - envName: GCP_PROJECT
       secretName: airflow-ch18-env
       secretKey: GCP_PROJECT
     - envName: MOVIELENS_USER
       secretName: airflow-ch18-env
       secretKey: MOVIELENS_USER
     - envName: MOVIELENS_PASSWORD
       secretName: airflow-ch18-env
       secretKey: MOVIELENS_PASSWORD
   ```
3. redeploy:
   ```shell
   helm upgrade --install airflow apache-airflow/airflow -n airflow -f resources/helm-override.yaml --debug
   ```

The airflow deployment should now have access to the environment
variables it needs. There is still one thing we need to do
to make our DAG run succesfully. We need to deploy our
`movielens-api`.
I assume that you have a Google Cloud Platform service account
added through the webserver UI.

## But there is more
We need to have our movielens-api service exposed on GCP
and as part of the cluster so we can actually run the first task.
So, basically you need to add the connection id and build the
movielens-api service and deploy it.

The following commands should work:
1. navigate to `chapter08/movielens-api` and execute the
following command to build the image:
   ```shell
   docker build -t europe-west4-docker.pkg.dev/<project-id>/airflow-gke/movielens-api:latest .
   ```
2. publish the image:
   ```shell
   docker push europe-west4-docker.pkg.dev/<project-id>/airflow-gke/movielens-api:latest
   ```
3. create the secrets that movielens-api needs:
   ```shell
   kubectl create secret generic movielenssecret --from-literal=API_USER=airflow --from-literal=API_PASSWORD=airflow -n airflow
   ```
4. navigate to `chapter18`.
5. deploy the movielens-api service. I prepared the
`movielens-deployment.yaml` for this purpose. Check it out.
6. run the following command to deploy movielens-api:
   ```shell
   kubectl apply -f resources/movielens-deployment.yaml -n airflow
   ```
7. go to the `webserver > admin > connections` and add the
movielens connection id. The host should be `movielens-api`.
I believe you know the rest of the data.

Right now, when you run your DAG all should work ok :-)
Again, if memory serves correctly.

## Enabling logging to Google Cloud Storage
Although the DAG should run correctly, when you try to access
the logs from the webserver UI you may find that you are unable
to view the logs. So, I spent some time and managed to enable
them on my deployment.

So let's get started:
1. create another service account through the GCP console.
I named mine: `airflow-logs`.
2. create a bucket for the logs. I named mine: `airflow_logs_mac`
3. make sure that the service account has read, write and delete
privileges on the created bucket. Storage object Admin should
be sufficient.
4. create a service account key and download it.
5. create a secret using the service account json file you just.
I downloaed. I named my secret `cad`.
   ```shell
   kubectl create secret generic cad --from-file=key.json=/<path>/<to>/<json>/<file.json> -n airflow
   ```
6. enable remote logging for airflow. I have done this (again)
in the `helm-override.yaml` file. The following part of the
yaml does this:
   ````yaml
   config:
     logging:
       remote_logging: 'True'
       remote_base_log_folder: 'gs://<logs_bucket_name>/airflow/logs/'
       remote_log_conn_id: 'cad'
       google_key_path:  "/opt/airflow/secrets/key.json"
     webserver:
       expose_config: 'True'
   ````
   replace the `remote_log_conn_id` and `remote_base_log_folder`
   values if needed. Expose config is set to `True` for
   debugging purposes. The `google_key_path` is the path on
   which we will mount our secret key json file.
7. We still need to mount the volume with the credentials we
stored in the `key.json` secret. I mounted the secret
on the webserver, scheduler, triggerer and workers. The
following is the example for scheduler:
   ```yaml
   scheduler:
     extraVolumeMounts:
       - name: google-cloud-key
         mountPath: /opt/airflow/secrets
     extraVolumes:
       - name: google-cloud-key
         secret:
           secretName: cad
   ```
   You can check out how the volume is mounted on the rest
   of the services.

The logs should hopefully work now.

Myself, I had to create a new project and start over as I
probably messed up something while learning.
