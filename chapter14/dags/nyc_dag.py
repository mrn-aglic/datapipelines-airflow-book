import json

import requests
from airflow import DAG
from airflow.hooks.base import BaseHook
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.dates import days_ago
from requests.auth import HTTPBasicAuth


def _download_citibike_data(ts_nodash, **_):
    citibike_conn = BaseHook.get_connection(conn_id="citibike")

    url = f"http://{citibike_conn.host}:{citibike_conn.port}/recent/minute/15"
    response = requests.get(
        url, auth=HTTPBasicAuth(citibike_conn.login, citibike_conn.password)
    )

    data = response.json()

    s3_hook = S3Hook(aws_conn_id="s3")

    s3_hook.load_string(
        string_data=json.dumps(data),
        key=f"raw/citibike/{ts_nodash}.json",
        bucket_name=Variable.get("MC_BUCKET_NAME"),
    )


dag = DAG(
    dag_id="nyc_dag",
    start_date=days_ago(1),
    schedule_interval="*/15 * * * *",
    catchup=False,
)

download_citibike_data = PythonOperator(
    task_id="download_citibike_data", python_callable=_download_citibike_data, dag=dag
)
