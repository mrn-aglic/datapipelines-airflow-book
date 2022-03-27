# Chapter 17 - Airflow on Azure

This Readme is taken directly from the book [GitHub repo](https://github.com/BasPH/data-pipelines-with-apache-airflow).

I ran into some issue with using OPENROWSET with azure Synapse.
To successfully run the code, you need to do the following:
1. go to portal.azure and go to storage acount overview
2. then go to Shared Access Signature and click on
_Generate SAS and connection string_. This will generate a SAS
token amongst other things. Copy the SAS token.
3. Ok, now return Home and go to synapse workspace.
4. Open Synapse studio and create an SQL script.
5. Copy the contents of the file from resources -> credential.sql
6. Finish the name of the credential (mine was marinairflowazure).
7. And paste the SAS token that you generated in step 2. However,
remove the "?" at the beginning.
8. Copy the finished script contents to the script in the Synapse
studion and execute.
9. You're good to go!

Code accompanying Chapter 17 of the book 'Data pipelines with Apache Airflow'.

## Contents

This code example contains the following files:

```
├── dags
│   ├── 01_azure_usecase.py      # The actual DAG.
│   └── custom                   # Code supporting the DAG.
│       ├── __init__.py
│       └── hooks.py
├── docker
│   └── airflow-azure            # Custom Airflow image with the required depedencies.
├── docker-compose.yml           # Docker-compose file for Airflow.
└──  readme.md                   # This file.
```

## Usage

To get started with the code example, first use the Azure Portal to create the following required resources for the DAG:

* Resource group
* Synapse workspace
* Blob storage containers

How to create these resources (+ what settings to used) is described in the Chapter.

Once the required resources have been created, rename the file .env.template to .env and enter the details of the created resources.

Once this is all set up, you can start Airflow using:

    docker-compose up --build

Once you're done, you can tear down Airflow using:

    docker compose down -v

Don't forget to clean up your Azure resources by deleting the created stack.
