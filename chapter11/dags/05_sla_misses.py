# sla - service level agreement
from datetime import timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils import dates as date_utils


def sla_miss_callback(context):
    print("Missed SLA!")
    send_slack_message("Missed SLA!")


def send_slack_message(message):
    pass


default_args = {
    "owner": "test",
    "sla": timedelta(seconds=1),
    "email": ["example@example.com"],
}

with DAG(
    dag_id="05_sla_misses",
    start_date=date_utils.days_ago(15),
    schedule_interval="@daily",
    default_args=default_args,
    sla_miss_callback=sla_miss_callback,
) as dag:
    sleep_task = BashOperator(task_id="sleep", bash_command="sleep 10")
