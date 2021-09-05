from pathlib import Path

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.python import PythonSensor
from airflow.utils import dates

dag1 = DAG(
    dag_id="04_ingesting_supermarket_data",
    start_date=dates.days_ago(3),
    schedule_interval="0 16 * * *",
)

dag2 = DAG(
    dag_id="04_dag02",
    start_date=dates.days_ago(3),
    schedule_interval=None,
)


def _wait_for_supermarket(supermarket_id):
    supermarket_path = Path("/data/" + supermarket_id)
    data_files = supermarket_path.glob("data-*.csv")
    success_file = supermarket_path / "_SUCCESS"
    return data_files and success_file.exists()


for market_id in range(1, 5):
    wait = PythonSensor(
        task_id=f"wait_for_supermarket_{market_id}",
        python_callable=_wait_for_supermarket,
        op_kwargs={"supermarket_id": f"supermarket{market_id}"},
    )

    copy = DummyOperator(task_id=f"copy_to_raw_supermarket_{market_id}", dag=dag1)
    process = DummyOperator(task_id=f"process_supermarket_{market_id}", dag=dag1)
    trigger_create_metrics_dag = TriggerDagRunOperator(
        task_id=f"trigger_create_metrics_dag_supermarket_{market_id}",
        trigger_dag_id="04_dag02",
        dag=dag1,
    )
    wait >> copy >> process >> trigger_create_metrics_dag

compute_differences = DummyOperator(task_id="compute_differences", dag=dag2)
update_dashboard = DummyOperator(task_id="update_dashboard", dag=dag2)
notify_new_data = DummyOperator(task_id="notify_new_data", dag=dag2)
compute_differences >> update_dashboard
