import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils import dates


def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    print("Missed SLA!")
    send_slack_message("Missed SLA!")


def send_slack_message(message):
    pass


dag = DAG(
    dag_id="ch12-task_sla",
    default_args={"email": "mrn.aglic@gmail.com"},
    # schedule_interval="@daily",
    schedule_interval=datetime.timedelta(hours=12),
    sla_miss_callback=sla_miss_callback,
    start_date=dates.days_ago(3),
)

sleeptask = BashOperator(
    task_id="sleep", bash_command="sleep 5", sla=datetime.timedelta(seconds=1), dag=dag
)
