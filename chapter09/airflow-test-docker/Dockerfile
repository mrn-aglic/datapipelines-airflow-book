FROM python:3.8-slim

RUN apt-get -y update
RUN apt-get -y install git sqlite3
RUN pip install "apache-airflow[celery]==2.2.2" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.2.2/constraints-3.8.txt"
RUN pip install pytest pytest-mock pytest-docker-tools
RUN python -m pip install --upgrade git+https://github.com/mrn-aglic/airflow_book_example_package_repo

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
