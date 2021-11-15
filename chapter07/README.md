# Chapter 07 guide

Chapter 07 of the book
_Data Pipelines with Apache Airflow_
by manning is somewhat more difficult than the other
chapters. This is because it requires the reader to use
some external services.

I'm going to try and explain what I did and why I did it.

The entire folder is basically split into two parts:
1. digit_classifier - which has some extra examples and
including that example the digit classifier example
(in short until chapter 7.2). Note that I kept minio
in the docker-compose file and some DAGs that use it.
What you really need if you follow the book is an `aws
account`. The `digit classifier` example cannot be
completed without it. A partial implementation that uses
minio is provided.
2. inside_airbnb - which starts from chapter 7.2.

# Digit classifier example

## pre-requirements
If you want to run sagemaker operators you're going to
need an aws account. You can get a free tier account.
Also, make sure you have a bucket that you want to use
and that you set the correct name of the bucket
in the variable `my_bucket` in the DAGs.

## Starting up
You probably have docker installed already, and I assume
you know how to use it.

The docker-compose file contains two services `locals3`
and `locals3_init` that are required to to run minio, a
local s3 object storage. Some dags use minio, some don't.
The dags that use minio are:
- 01_s3_copy_object_fixed (01_s3_copy_object.py)
- _setup_env_dag
- digit_classifier

The commands in these services have been modified compared
to the book. For starters, newer images are used.

**NOTE that in the book minio is not introduced until
chapter 7.2. (insider airbnb).**

**YOU DO NOT NEED MINIO FOR THE FIRST PART OF THE
CHAPTER AND YOU CAN SAFELY DELETE THE SERVICES FROM
DOCKER-COMPOSE.YML IF YOU DO NOT PLAN TO RUN THE
DAGs THAT DEPEND ON IT.**

## Locals3 service
The locals3 service also has a different command since
minio now requires us to specify the console address:
```
command: server --console-address ":9001" /data
```
We also needed to change the credentials for this
service. So, these two lines are also different
than in the book:
```
environment:
      - MINIO_ROOT_USER=user
      - MINIO_ROOT_PASSWORD=password
```

## LocalS3_init service

The entrypoint for `locals3_init` is also modified:
```dockerfile
entrypoint: >
      /bin/sh -c "
      while ! /usr/bin/mc config host add locals3 http://locals3:9000 user password; do echo 'MinIO not up and running yet...' && sleep 1; done;
      echo 'Added mc host config.';
      /usr/bin/mc mb locals3/data;
      /usr/bin/mc mb locals3/data-backup;
      /usr/bin/mc mb locals3/sagemaker-sample-data-eu-west-1;
      /usr/bin/mc cp --attr key=algorithms/kmeans/mnist/mnist.pkl.gz dataset/mnist.pkl.gz locals3/sagemaker-sample-data-eu-west-1;
      exit 0;
      "
```
The first two lines are as in the book and add host
config.
The next three lines create buckets in locals3 which
are used by DAGs. Don't worry,
if the buckets already exist, you will just get a
notification about it in the console.

The last line is to copy the mnist data, that I already
downloaded from aws, to minio bucket. However,
this command doesn't work. There seems to be some
problem with the cp command at the time I'm writing
this.

The environment variables are also somewhat modified.
Here they are:
```
  - AIRFLOW_CONN_LOCALS3=s3://user:password@?host=http%3A%2F%2Flocals3%3A9000
  - AIRFLOW__CORE__ENABLE_XCOM_PICKLING=True
```
The first one ads the locals3 connection id to the
environment. Note that the format is:
```
s3://<root_user:root_password>@?host=http%3A%2F%2Flocals3%3A9000
```
Note that the URL needs to be URL encoded. If you
decided to add you're own URL, keep this in mind.
The issue is described [here](url=https://stackoverflow.com/questions/69079916/how-to-connect-airflow-to-minio-s3?noredirect=1#comment122102111_69079916)
in more detail.

The second line fixes a pickling issue with the
`SageMakerTrainingOperator` operator. The issue is active
at the time I'm writing this. You can find it on
[github](url=https://github.com/apache/airflow/issues/16386).

## The .env file and using aws
If you do not plan to run DAGs that use aws or sagemaker,
you don't need an `.env` file.
Simply make the appropriate changes in
`docker-compose.yml`.
Otherwise, read on.

If you want to use the DAGs that use aws, you need
to add your own connection string for aws.
I have premade a `.env_backup` file. Rename this file
to `.env`.

First define the `aws_conn` connection id. To do this,
you need to create an access key. You can create
a key for the root user or a new one.
To add an access key to your root user, login to aws
console with the root user credentials and open the
dropdown for your account and click on the `My security
credentials` option.

If you are creating a new user, choose `Access key - Programmatic
access` which will automatically generate an access key
In the `.env` file, set the variable:
```
AIRFLOW_CONN_AWS_CONN=aws://<access_key_id>:<secret_access_key>
```

The sagemaker operator `SageMakerTrainingOperator`
requires you to define a default aws region,
which i do through the .env file:
```
AWS_DEFAULT_REGION=eu-west-1
```

I have not tested whether other operators require
this variable.
**Also note that the default region must be the same
as the one from which you pull the image for the
sagemaker operator!!**
You can find a list of these images [here](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-algo-docker-registry-paths.html).

If you want to run the chalice example, you'll also
need the `.env.chalice` environment file you can get
by renaming and modyfing `.env_backup.chalice`

## Using sagemaker
Ok, so, to use sagemaker operators, you need to create a
role with the appropriate policy in order to get a
Role arn for sagemaker.

Go to aws console and first create a policy. You can
find the policy used by me in the `aws_resources` folder.
This policy basically allows everything for S3 (I'm an aws
beginner). ~~Do not forget to also assign the
`AmazonSageMakerFullAccess` policy to the role! Otherwise
the sagemaker deployment task won't work.~~ (doesn't
seem to be necessery)

Afterwards, create a role and attach the policy to it.
Paste the Role ARN variable to the sagemaker config
constant `SAGEMAKER_CONFIG` under the `"role_arn"` key.

### A note on SageMakerEndpointOperator
The task using this operator may take up to 5-6 minutes
so be patient.
Note that the model names in the config, under the paths
`Model.ModelName` and `Endpoint.ModelName`
must match for the **create** operation.
The operator did not work for me any other way. For the
**update** operation the `Model.ModelName` must not
exist in your aws account. I tried it.

## The _setup_env_dag
This DAG needs to be run once in order to use
minio local s3 for some of the other DAGs. You can run
it multiple times without worry of errors (tested it).

The DAG does two (number two is disabled) things:
1. copies the mnist.pkl.gz file from local file system
to the minio instance s3 bucket. Note that this
functionality can be removed once minio client starts
working properly. Read _LocalS3_init_ service section.
2. Adds `aws_conn` connection id to the airflow
UI if it is not present there. **This doesn't seem to be
necessery at all**. However, I needed it when I first
added the connection string to the `.env` file.
Probably because part of the connection string was not
URL encoded. <br/> **_I'm really not sure why it worked
when added to UI and with only part of the
connection string URL encoded_**. <br/> **In summary, you
most likely won't need to run this part of the DAG.**

## DAGs in this part (folder)
1. _setup_env_dag - use this DAG to setup some pre
requirements for using minio local s3.
2. 01_s3_copy_object - this DAG creates in the minio s3
bucket.
3. digit_classifier - this DAG uses local s3 instance,
which unfortunately doesn't have access to sagemaker
4. digit_classifier_aws - the same as 3, but uses
aws connection to use sagemaker.

# Insider airbnb example

## DAGs in this part (from chapter 7.2)
1. test_dag - just to check that the aws connection
string can work without being added to the UI
2. inside_airbnb - the example from the book using
PythonOperator
3. inside_airbnb_docker - as number 2, but the
numbercruncher is inside a docker container.

## DockerOperator prerequisites
IN order to use the `inside_airbnb_docker` DAG, the
DockerOperator requires access to the file:
`/var/run/docker.sock`.
This repo contains two solutions that work for OS X.
I'm not sure whether they will work for other operating
systems.

The "cleaner" solution is to add an additional service
that crates a relay for bidirectional data transfer.
Here is the service added to docker-compose:
```
socat:
    image: alpine/socat
    command: tcp-listen:2375,fork,reuseaddr unix-connect:/var/run/docker.sock
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    expose:
      - "2375"
```

Additionally, to use the service the scheduler and
webserver are linked to it and an additional environment
variable is added:
```dockerfile
webserver:
    ...
    environment:
      <<: *airflow_environment
      DOCKER_HOST: tcp://socat:2376
    links:
      - socat
    ...
```
```dockerfile
scheduler:
    ...
    environment:
      <<: *airflow_environment
      DOCKER_HOST: tcp://socat:2376
    links:
      - socat
    ...
```
In the DAG itself, we define that the DockerOperator:
```python
access_key = os.environ.get("S3_ACCESS_KEY")
secret_key = os.environ.get("S3_SECRET_KEY")

docker_host = os.environ.get("DOCKER_HOST")

crunch_numbers = DockerOperator(
    task_id="crunch_numbers",
    image="airflow_book/numbercruncher",
    api_version="auto",
    auto_remove=True,
    # docker_url="unix://var/run/docker.sock",
    docker_url=docker_host,
    network_mode="host",
    environment={
        "S3_ENDPOINT": "localhost:9000",
        "S3_ACCESS_KEY": access_key,
        "S3_SECRET_KEY": secret_key,
    },
    dag=dag,
)
```

### Second solution for docker.sock
The other solution is to mount the docker.sock on the
scheduler and webserver services and grant
airflow permission to use the file.

First, we mount the volume for docker.sock in
docker-compose as given below and setup an additional
argument that will be passed to the Dockerfile:
```dockerfile
webserver:
    build:
      context: airflow
      args:
        AIRFLOW_BASE_IMAGE: *airflow_image
        AIRFLOW_CMD: webserver
    ...
    volumes:
      - logs:/opt/airflow/logs
      - /var/run/docker.sock:/var/run/docker.sock
    environment: *airflow_environment
    ...
    command: webserver
```

In the Dockerfile for the airflow webserver and
scheduler services, we need to setup the script
that will be run once the containers are started
and export the airflow command as an environment
variable:

```dockerfile
ARG AIRFLOW_CMD
ENV AIRFLOW_CMD=${AIRFLOW_CMD}

COPY entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

Finally, the `entrypoint.sh` script is as follows:
```shell
#!/usr/bin/env bash
chown -R airflow /var/run/docker.sock

printenv AIRFLOW_CMD
su airflow -c "/usr/bin/dumb-init -- /entrypoint $AIRFLOW_CMD"
```

# THE END... finally
It took me about two months of my free time to get
through the entire chapter and get everything to work.
After completing the first part of the chapter
I understood that I wasted my time with minio since
aws was mandatory for that part. However, minio is still
required for the second part (insideairbnb).

Oh well... hope this will help someone who is confused
by the chapter as I was.
