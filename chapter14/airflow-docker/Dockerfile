ARG AIRFLOW_BASE_IMAGE="apache/airflow:2.2.2-python3.8"
FROM ${AIRFLOW_BASE_IMAGE}

USER root

RUN apt-get -y update
RUN apt-get -y install git

USER airflow
RUN python -m pip install --upgrade git+https://github.com/mrn-aglic/nyc_operators.git
RUN pip install --user --no-cache-dir \
    minio \
    geopandas
