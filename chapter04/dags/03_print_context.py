import pprint as pp

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils import dates

dag = DAG(
    dag_id="03_print_context",
    start_date=dates.days_ago(3),
    schedule_interval="@daily",
)


def _print_context(**kwargs):
    pp.pprint(kwargs)


print_context = PythonOperator(
    task_id="print_context",
    python_callable=_print_context,
    dag=dag,
)
