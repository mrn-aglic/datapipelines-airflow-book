ARG AIRFLOW_BASE_IMAGE
FROM ${AIRFLOW_BASE_IMAGE}

RUN pip install --user --no-cache-dir \
    apache-airflow-providers-amazon

USER root
RUN mkdir /dataset

COPY ../dataset/ /dataset/
RUN echo $(ls /dataset)

USER airflow
