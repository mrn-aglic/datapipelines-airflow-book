from pathlib import Path

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.sensors.python import PythonSensor
from airflow.utils import dates

dag = DAG(
    dag_id="figure_06",
    start_date=dates.days_ago(3),
    schedule_interval="0 16 * * *",
    description="A batch workflow for ingesting supermarket promotions data, demonstrating the FileSensor.",
    default_args={"depends_on_past": True},
)


def _wait_for_supermarket(supermarket_id):
    supermarket_path = Path(f"/data/{supermarket_id}")
    data_files = supermarket_path.glob("data-*.csv")
    success_file = supermarket_path / "_SUCCESS"
    return data_files and success_file.exists()


create_metrics = DummyOperator(task_id="create_metrics")

for market_id in range(1, 5):
    wait = PythonSensor(
        task_id=f"wait_for_supermarket_{market_id}",
        python_callable=_wait_for_supermarket,
        op_kwargs={"supermarket_id": f"supermarket{market_id}"},
        timeout=600,
        dag=dag,
    )

    copy = DummyOperator(task_id=f"copy_to_raw_supermarket_{market_id}", dag=dag)
    process = DummyOperator(task_id=f"process_supermarket_{market_id}", dag=dag)
    wait >> copy >> process >> create_metrics
