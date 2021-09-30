#Chapter 07 guide

Chapter 07 of the book Datapipelines with apache airflow
by manning is somewhat more difficult than the other
chapters. This is because it requires the reader to use
some external services.

I'm going to try and explain what I did and why I did it.

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

The commands in these services have been modified compared
to the book. For starters, newer images are used.

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
```
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


## Using sagemaker
Ok, so, to use sagemaker operators, you need to create a
role with the appropriate policy in order to get a
Role arn for sagemaker.

Go to aws console and first create a policy. You can
find the policy used by me in the `aws_resources` folder.
This policy basically allows everything (I'm an aws
beginner).

Afterwards, create a role and attach the policy to it.
Paste the Role ARN variable to the sagemaker config
constant `SAGEMAKER_CONFIG` under the `"role_arn"` key.

## The _setup_env_dag
This DAG needs to be run once in order to use
minio local s3 for some of the other DAGs. You can run
it multiple times without worry of errors (tested it).

The DAG does two things:
1. copies the mnist.pkl.gz file from local file system
to the minio instance s3 bucket. Note that this
functionality can be removed once minio client starts
working properly. Read _LocalS3_init_ service section.
2. For some odd reason, the `aws_conn` connection id
cannot be used if only defined as an environment
variable. The conn id needs to be visible from airflow
UI, which is why the second functionality tests whether
aws_conn is present in the `settings.Session` of airflow,
and if not, adds it.

## DAGs in this chapter
1. _setup_env_dag - use this DAG to setup some pre
requirements for using minio local s3.
2. 01_s3_copy_object - this DAG creates in the minio s3
bucket.
3. digit_classifier - this DAG uses local s3 instance,
which unfortunately doesn't have access to sagemaker
4. digit_classifier_aws - the same as 3, but uses
aws connection to use sagemaker.
