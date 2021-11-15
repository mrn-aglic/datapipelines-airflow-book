#!/usr/bin/env bash
chown -R airflow /var/run/docker.sock

printenv AIRFLOW_CMD
su airflow -c "/usr/bin/dumb-init -- /entrypoint $AIRFLOW_CMD"
