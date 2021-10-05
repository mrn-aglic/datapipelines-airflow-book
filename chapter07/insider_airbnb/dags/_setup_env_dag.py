from airflow import DAG, settings
from airflow.models import Connection
from airflow.operators.bash import BashOperator
from airflow.operators.python import ShortCircuitOperator
from airflow.utils import dates

dag = DAG(
    dag_id="RUN_FIRST_setup_env",
    schedule_interval=None,
    start_date=dates.days_ago(1),
)


def _check_aws_conn_exists():
    connections = settings.Session.query(Connection)
    connection_ids = [conn.conn_id for conn in connections]
    conn_exists = "aws_conn" in connection_ids

    if conn_exists:
        print("connection already exists, skipping upstream task")

    return not conn_exists


short_circuit_aws_conn = ShortCircuitOperator(
    task_id="conditional_continue_aws_conn",
    python_callable=_check_aws_conn_exists,
    dag=dag,
)

# Add the aws_conn to the UI. For some reason, the aws_conn doesn't work if
# it is not added through the UI
add_aws_conn = BashOperator(
    task_id="add_aws_conn",
    bash_command="airflow connections add aws_conn --conn-uri $AIRFLOW_CONN_AWS_CONN",
    dag=dag,
)

short_circuit_aws_conn >> add_aws_conn
