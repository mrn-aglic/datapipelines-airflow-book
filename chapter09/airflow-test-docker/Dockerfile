FROM python:3.8-slim

RUN pip install pytest
RUN pip install "apache-airflow[celery]==2.2.2" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.2.2/constraints-3.8.txt"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
