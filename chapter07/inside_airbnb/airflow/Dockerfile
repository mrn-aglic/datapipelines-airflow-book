ARG AIRFLOW_BASE_IMAGE
FROM ${AIRFLOW_BASE_IMAGE}

RUN pip install --user --no-cache-dir \
    minio

# Uncomment the lines below to fix permission problem on docker.sock

#ARG AIRFLOW_CMD
#ENV AIRFLOW_CMD=${AIRFLOW_CMD}
#
#COPY entrypoint.sh /entrypoint.sh
#USER root
#RUN chmod +x /entrypoint.sh
#
#ENTRYPOINT ["/entrypoint.sh"]
