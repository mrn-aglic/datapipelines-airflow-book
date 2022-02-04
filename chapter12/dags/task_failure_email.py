from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago


def send_error():
    print("ERROR!")


dag = DAG(
    dag_id="chapter12_task_failure_email",
    default_args={"email": "myname@gmail.com"},
    on_failure_callback=send_error,
    schedule_interval=None,
    start_date=days_ago(3),
)

failing_task = BashOperator(
    task_id="failure",
    bash_command="exit 1",
    dag=dag,
)
