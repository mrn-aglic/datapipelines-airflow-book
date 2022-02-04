from airflow.models import DAG
from airflow.utils.dates import days_ago


def send_error():
    print("ERROR")


dag = DAG(
    dag_id="chapter12_dag_failure_callback",
    on_failure_callback=send_error,
    schedule_interval=None,
    start_date=days_ago(3),
)
