from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils import dates

dag = DAG(
    dag_id="07_print_dag_run_conf",
    start_date=dates.days_ago(3),
    schedule_interval=None,
)


def print_conf(**context):
    print("test")
    print(context["dag_run"].conf)


process = PythonOperator(
    task_id="process",
    python_callable=print_conf,
    dag=dag,
)
