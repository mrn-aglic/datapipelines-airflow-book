import datetime

import airflow.utils.dates
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.sensors.external_task import ExternalTaskSensor

dag1 = DAG(
    dag_id="figure_20_dag_1",
    start_date=airflow.utils.dates.days_ago(3),
    schedule_interval="0 16 * * *",
)
dag2 = DAG(
    dag_id="figure_20_dag_2",
    start_date=airflow.utils.dates.days_ago(3),
    schedule_interval="0 20 * * *",
)

# pylint: disable=expression-not-assigned
DummyOperator(task_id="copy_to_raw", dag=dag1) >> DummyOperator(
    task_id="process_supermarket", dag=dag1
)

wait = ExternalTaskSensor(
    task_id="wait_for_process_supermarket",
    external_dag_id="figure_20_dag_1",
    external_task_id="process_supermarket",
    execution_delta=datetime.timedelta(
        hours=4
    ),  # the execution times of dag1 and dag2 must match when
    # when the delta is subtracted from the dag2 schedule interval
    # to specify a list of time deltas try: execution_date_fn
    # function that receives the current execution date and returns the desired execution dates to query.
    # Either execution_delta or execution_date_fn can be passed to ExternalTaskSensor, but not both.
    dag=dag2,
)
report = DummyOperator(task_id="report", dag=dag2)
wait >> report
