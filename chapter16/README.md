# Chapter 16 - Airflow on AWS

This Readme is taken directly from the [book GitHub repo](https://github.com/BasPH/data-pipelines-with-apache-airflow).
Just makes sure that the aws secret you generate doesn't
have any special characters: +, / or %.

Additionally, I added an extra env variable `PROVIDED_CRAWLER`
that allows you to choose which trigger crawler the DAG will use.
In your UI you can create a new variable called `USE_CRAWLER`
which will take precedence over the `PROVIDER_CRAWLER` variable.
Both variables should contain the name of the next task
that is to be executed, otherwise an exception will ne thrown.

To use the built in `GlueCrawlerOperator` you need to setup an extra
policy. The policy is added in resources/stack.yml:

`- glue:GetCrawlerMetrics`

Code accompanying Chapter 16 of the book 'Data pipelines with Apache Airflow'.

## Contents

This code example contains the following files:

```
├── Makefile                     # Makefile for helping run commands.
├── dags
│   ├── 01_aws_usecase.py        # The actual DAG.
│   └── custom                   # Code supporting the DAG.
│       ├── __init__.py
│       ├── operators.py
│       └── hooks.py
├── docker
│   └── airflow-aws              # Custom Airflow image with the required depedencies.
├── docker-compose.yml           # Docker-compose file for Airflow.
├── readme.md                    # This file.
└── resources
    └── stack.yml                # CloudFormation template for AWS resources required for
```

## Usage

To get started with the code example, head over to the CloudFormation section in the AWS Console and use the provided CloudFormation template (*resources/stack.yml*) to create the required AWS resources. See the description in the Chapter for more details how to do so, if you're not yet familiar with the process.

Once the CloudFormation stack has been created, rename the file .env.template to .env and enter the details of the created resources. You should be able to get the bucket + crawler names from the CloudFormation stack resources tab. Don't forget to also create an access key/secret for the created user and include this in the .env file too.

Once this is all set up, you can start Airflow using:

    docker-compose up --build

Once you're done, you can tear down Airflow using:

    docker compose down -v

**Don't forget to clean up your AWS resources by deleting the created stack.**
