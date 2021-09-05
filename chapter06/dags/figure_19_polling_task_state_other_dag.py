from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils import dates

dag1 = DAG(
    dag_id="figure_19_dag_1",
    start_date=dates.days_ago(3),
    schedule_interval="0 0 * * *",
)
dag2 = DAG(
    dag_id="figure_19_dag_2",
    start_date=dates.days_ago(3),
    schedule_interval="0 0 * * *",
)

dag3 = DAG(
    dag_id="figure_19_dag_3",
    start_date=dates.days_ago(3),
    schedule_interval="0 0 * * *",
)

dag4 = DAG(
    dag_id="figure_19_dag_4",
    start_date=dates.days_ago(3),
    schedule_interval=None,
)

DummyOperator(task_id="etl", dag=dag1)
DummyOperator(task_id="etl", dag=dag2)
DummyOperator(task_id="etl", dag=dag3)

sensors = []

for i in range(1, 4):
    external_sensor = ExternalTaskSensor(
        task_id=f"wait_for_etl_dag{i}",
        external_dag_id=f"figure_19_dag_{i}",
        external_task_id="etl",
        dag=dag4,
    )
    sensors.append(external_sensor)

# pylint: disable=expression-not-assigned
sensors >> PythonOperator(
    task_id="report", dag=dag4, python_callable=lambda: print("Hello!")
)
