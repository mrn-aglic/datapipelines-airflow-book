from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id="hello_airflow",
    start_date=days_ago(3),
    max_active_runs=3,
    schedule_interval="@daily",
) as dag:

    print_hello = BashOperator(task_id="print_hello", bash_command="echo 'hello'")

    print_airflow = PythonOperator(
        task_id="print_airflow", python_callable=lambda: print("airflow")
    )

    print_hello >> print_airflow
